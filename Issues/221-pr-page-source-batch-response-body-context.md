# PR Draft: Validate Batched Page Source Response Bodies

## Summary

`PageCollection.get_page_sources()` batches `viewsource/ViewSourceModule` requests for pages whose source is still uncached, preserves successful source results when some batch entries fail retry, and already preserves later successes when one response is structurally malformed after body parsing. The remaining malformed response-body path still read `response.json()["body"]`, so an AMC response without a `body` field leaked a raw `KeyError` and aborted the loop before later successful source responses could be applied.

This follow-up keeps page-ID acquisition, cached source reuse, duplicate page-ID grouping, retry-exhausted `None` partial-success behavior, source wrapper parsing, `&nbsp;` normalization, multiline source extraction, and lazy `Page.source` behavior unchanged. It only treats batched page source responses without JSON `body` fields as malformed source responses, records a site/page/id-context `NoElementException`, continues processing later successful responses, and raises the first structural source error after the batch.

## Related Issue

Builds on [003-pr-batched-source-fetch.md](003-pr-batched-source-fetch.md), [007-pr-retry-source-fetch.md](007-pr-retry-source-fetch.md), [009-pr-cache-aware-source-fetch.md](009-pr-cache-aware-source-fetch.md), [016-pr-viewsource-multiline-text.md](016-pr-viewsource-multiline-text.md), [028-pr-source-iterator-fallback.md](028-pr-source-iterator-fallback.md), [034-pr-page-source-failure-context.md](034-pr-page-source-failure-context.md), [035-pr-source-iterator-parse-failure.md](035-pr-source-iterator-parse-failure.md), [037-pr-page-source-result-wiki-text.md](037-pr-page-source-result-wiki-text.md), [098-pr-page-source-failure-site-context.md](098-pr-page-source-failure-site-context.md), and [100-pr-page-source-parser-site-context.md](100-pr-page-source-parser-site-context.md). Those drafts established page source batching as a practical partial-success workflow with cached-source reuse and page-context diagnostics.

No upstream issue was filed from this local workspace.

## Changes

- Read batched page source response bodies with `response.json().get("body")`.
- Convert missing `viewsource/ViewSourceModule` response `body` fields into `NoElementException` with site, page, and page ID context.
- Preserve later successful source responses in the same batch after a missing-body response.
- Preserve retry-exhausted `None` responses as skipped partial-success entries.
- Preserve cached source reuse, duplicate page-ID grouping, page-ID acquisition, source wrapper parsing, `&nbsp;` normalization, multiline source extraction, and lazy source behavior.
- Add a focused regression for a missing middle source response body that still applies later successful source text.

## Type Of Change

- Bug fix / diagnostics improvement
- Page source batch response validation
- Partial-success preservation
- Test coverage

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| A batched page source response without JSON `body` fails before source-wrapper parsing. | `TestPageCollectionAcquire.test_acquire_sources_missing_response_body_preserves_later_successes_with_page_context` returns `{}` for a middle source response and expects `NoElementException`. | A change that raises raw `KeyError`, fabricates empty source text, or enters source-wrapper parsing for the malformed response rejects this local completion claim. |
| Malformed source response errors identify site, page, and page ID. | The focused regression asserts `Page source response body is not found for site: test-site, page: missing-body-page (id=222)`. | An exception without site/page/id context rejects this local completion claim. |
| Later successful source responses remain applied after a malformed middle response. | The focused regression verifies the first and third pages receive `first source` and `third source` while the malformed page remains uncached. | A change that aborts before later successes, returns partial success without raising, or assigns source to the malformed page rejects this local completion claim. |
| Retry-exhausted `None` responses remain distinct from malformed response bodies. | Existing source partial-success retry test remains green and leaves failed retry pages uncached. | A change that turns retry exhaustion into body-validation failure rejects this local completion claim. |
| Existing collection acquisition behavior remains green. | `uv run pytest tests/unit/test_page.py::TestPageCollectionAcquire -q` passed 35 tests. | Regressions in page ID acquisition, cached source reuse, duplicate source reuse, revision/vote/file acquisition, or source parse behavior reject this local completion claim. |
| Page and adjacent site workflows remain green. | `uv run pytest tests/unit/test_page.py -q` passed 121 tests; `uv run pytest tests/unit/test_page.py tests/unit/test_page_file.py tests/unit/test_page_revision.py tests/unit/test_page_votes.py tests/unit/test_site.py -q` passed 268 tests. | Regressions in page source/revision/vote/file/site flows reject this local completion claim. |
| Broad unit and static quality gates remain green. | `uv run pytest tests/unit -q`; `uv run ruff format src tests`; `uv run ruff check src tests`; `uv run ruff format --check src tests`; `uv run mypy src tests`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject this local completion claim. |

## Testing

Implemented locally in commit `0d3a700 fix(page): validate batched source response bodies`.

- RED: `uv run pytest tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_sources_missing_response_body_preserves_later_successes_with_page_context -q` failed before the fix with `KeyError: 'body'`.
- GREEN: `uv run pytest tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_sources_missing_response_body_preserves_later_successes_with_page_context -q` passed after the fix.
- `uv run pytest tests/unit/test_page.py::TestPageCollectionAcquire -q` passed 35 tests.
- `uv run pytest tests/unit/test_page.py -q` passed 121 tests.
- `uv run pytest tests/unit/test_page.py tests/unit/test_page_file.py tests/unit/test_page_revision.py tests/unit/test_page_votes.py tests/unit/test_site.py -q` passed 268 tests.
- `uv run pytest tests/unit -q` passed 764 tests.
- `uv run ruff format src tests` left 80 files unchanged.
- `uv run ruff check src tests`.
- `uv run ruff format --check src tests`.
- `uv run mypy src tests`.
- `git diff --check`.

Not run successfully: `pyright --version` because this environment could not find a `pyright` executable.

## Acceptance Criteria

- `PageCollection.get_page_sources()` still batches uncached page source requests by page ID.
- Cached source reuse and duplicate page-ID source reuse remain unchanged.
- Missing batched source response JSON `body` raises `NoElementException` naming the site, page, and page ID.
- Missing response-body handling does not convert retry-exhausted `None` responses into malformed-body failures.
- Later successful responses in the same source batch are still applied before the first structural source error is raised.
- Source wrapper parsing, `&nbsp;` normalization, multiline source extraction, lazy `Page.source`, and page source refresh behavior remain unchanged.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, non-goals, verification, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and the local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

Batched page source acquisition is a core read path for source verification and source iteration. If Wikidot returns one malformed generated-module response in a batch, wikidot.py should keep successful neighboring results and report a structured page-specific failure, not leak a raw dictionary `KeyError` or lose later source data.

## Local Evidence, Not For Upstream Paste

- Earlier local drafts established page source batching, retry-aware partial success, cached duplicate reuse, multiline ViewSource normalization, source iteration, and source parser context.
- Recent response-body validation slices across private-message, forum-post, forum-category, forum-thread, site-application, site-member, page-file, page-revision, forum-post-revision, recent-changes, page auxiliary, and ListPages modules showed the same raw `KeyError` failure mode at AMC response-body boundaries.
- The refreshed complexity memo continues to list raw response-body boundaries in page collection revision/vote/file batch helpers as follow-up leads after this slice removes the direct batched source raw body read.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, raw response JSON, generated source HTML, page source text, and site content out of upstream discussion.

## Additional Notes

This slice intentionally does not change request module names, request payloads, retry policy, retry-exhausted `None` handling, page-ID acquisition, cached source reuse, duplicate page-ID grouping, source wrapper parsing, `&nbsp;` normalization, multiline source extraction, lazy source reads, source refresh behavior, or live Wikidot behavior. It only converts missing batched source response `body` fields into site/page/id-context `NoElementException` failures while preserving later successes in the same batch.
