# PR Draft: Validate Batched Page Revision Response Bodies

## Summary

`PageCollection.get_page_revisions()` batches `history/PageRevisionListModule` requests for pages whose revision history is still uncached, reuses cached duplicate page-ID revisions, and parses revision rows into page-owned `PageRevisionCollection` objects. The remaining malformed response-body path still read `response.json()["body"]`, so an AMC response without a `body` field leaked a raw `KeyError` before the revision-list boundary could report which site and page produced the malformed response.

This follow-up keeps page-ID acquisition, cached revision reuse, duplicate page-ID cloning, request payloads, retry-exhausted `None` skip behavior, revision row parsing, user/date parsing, source/html clone preservation, and lazy `Page.revisions` behavior unchanged. It only treats batched revision-list responses without JSON `body` fields as malformed revision-list responses and raises `NoElementException` with site, page, and page ID context before BeautifulSoup parsing.

## Related Issue

Builds on [004-pr-batched-revision-vote-file-fetch.md](004-pr-batched-revision-vote-file-fetch.md), [019-pr-retry-page-revision-source-html.md](019-pr-retry-page-revision-source-html.md), [045-pr-page-revision-source-parse-context.md](045-pr-page-revision-source-parse-context.md), [103-pr-page-revision-parse-site-context.md](103-pr-page-revision-parse-site-context.md), [105-pr-page-revision-lazy-fetch-site-context.md](105-pr-page-revision-lazy-fetch-site-context.md), [120-pr-page-revision-response-body-context.md](120-pr-page-revision-response-body-context.md), and [216-pr-page-revision-response-body-context.md](216-pr-page-revision-response-body-context.md). Those drafts established page revision collection reads as cached, duplicate-aware, retry-aware workflows with revision parser context and response-body validation for revision source/HTML reads.

No upstream issue was filed from this local workspace.

## Changes

- Read batched page revision-list response bodies with `response.json().get("body")`.
- Convert missing `history/PageRevisionListModule` response `body` fields into `NoElementException` with site, page, and page ID context.
- Preserve retry-exhausted `None` responses as skipped entries.
- Preserve cached revision reuse, duplicate page-ID cloning, source/html clone preservation, revision row parsing, user parsing, date parsing, comment spacing, and lazy revisions behavior.
- Add a focused regression for missing batched revision-list response bodies through public `PageCollection.get_page_revisions()`.

## Type Of Change

- Bug fix / diagnostics improvement
- Page revision batch response validation
- Test coverage

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| A batched page revision-list response without JSON `body` fails before BeautifulSoup parsing. | `TestPageCollectionAcquire.test_acquire_revisions_missing_response_body_includes_site_page_context` returns `{}` from the revision-list response and expects `NoElementException`. | A change that raises raw `KeyError`, fabricates an empty revision collection, or enters revision row parsing rejects this local completion claim. |
| Malformed revision-list response errors identify site, page, and page ID. | The focused regression asserts `Page revision list response body is not found for site: test-site, page: test-page (id=...)`. | An exception without site/page/id context rejects this local completion claim. |
| Missing-body failure does not populate revisions. | The focused regression verifies `mock_page_with_id._revisions is None` after the malformed response. | A change that stores an empty or partial revision collection rejects this local completion claim. |
| Retry-exhausted `None` responses remain distinct from malformed response bodies. | Existing lazy retry-exhausted revisions tests and collection acquisition tests remain green. | A change that turns retry exhaustion into body-validation failure rejects this local completion claim. |
| Existing collection acquisition behavior remains green. | `uv run pytest tests/unit/test_page.py::TestPageCollectionAcquire -q` passed 36 tests. | Regressions in page ID acquisition, source acquisition, revision duplicate reuse, vote acquisition, file acquisition, or parser context reject this local completion claim. |
| Page and adjacent site workflows remain green. | `uv run pytest tests/unit/test_page.py -q` passed 122 tests; `uv run pytest tests/unit/test_page.py tests/unit/test_page_file.py tests/unit/test_page_revision.py tests/unit/test_page_votes.py tests/unit/test_site.py -q` passed 269 tests. | Regressions in page source/revision/vote/file/site flows reject this local completion claim. |
| Broad unit and static quality gates remain green. | `uv run pytest tests/unit -q`; `uv run ruff format src tests`; `uv run ruff check src tests`; `uv run ruff format --check src tests`; `uv run mypy src tests`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject this local completion claim. |

## Testing

Implemented locally in commit `b54f1ff fix(page): validate batched revision response bodies`.

- RED: `uv run pytest tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_revisions_missing_response_body_includes_site_page_context -q` failed before the fix with `KeyError: 'body'`.
- GREEN: `uv run pytest tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_revisions_missing_response_body_includes_site_page_context -q` passed after the fix.
- `uv run pytest tests/unit/test_page.py::TestPageCollectionAcquire -q` passed 36 tests.
- `uv run pytest tests/unit/test_page.py -q` passed 122 tests.
- `uv run pytest tests/unit/test_page.py tests/unit/test_page_file.py tests/unit/test_page_revision.py tests/unit/test_page_votes.py tests/unit/test_site.py -q` passed 269 tests.
- `uv run pytest tests/unit -q` passed 765 tests.
- `uv run ruff format src tests` left 80 files unchanged.
- `uv run ruff check src tests`.
- `uv run ruff format --check src tests`.
- `uv run mypy src tests`.
- `git diff --check`.

Not run successfully: `pyright --version` because this environment could not find a `pyright` executable.

## Acceptance Criteria

- `PageCollection.get_page_revisions()` still batches uncached page revision-list requests by page ID.
- Cached revision reuse, duplicate page-ID cloning, source/html clone preservation, revision row parsing, user/date parsing, and comment spacing remain unchanged.
- Missing batched revision-list response JSON `body` raises `NoElementException` naming the site, page, and page ID.
- Missing response-body handling does not convert retry-exhausted `None` responses into malformed-body failures.
- Malformed missing-body responses do not populate page revisions.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, non-goals, verification, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and the local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

Batched page revision acquisition is a common history read path. If Wikidot returns a malformed generated-module response, wikidot.py should report a structured site/page/id failure, not a raw dictionary `KeyError`, so caller logs can route the failure without preserving raw response JSON, generated history HTML, revision comments, credentials, or private site content.

## Local Evidence, Not For Upstream Paste

- Earlier local drafts established page revision collection batching, retry-aware revision source/HTML reads, duplicate revision clone behavior, and revision parser context.
- Recent response-body validation slices across private-message, forum-post, forum-category, forum-thread, site-application, site-member, page-file, page-revision source/HTML, forum-post-revision, recent-changes, page auxiliary, ListPages, and batched page source modules showed the same raw `KeyError` failure mode at AMC response-body boundaries.
- The refreshed complexity memo continues to list raw response-body boundaries in page collection vote/file batch helpers as follow-up leads after this slice removes the direct batched revision-list raw body read.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, raw response JSON, generated revision-list HTML, revision comments, and site content out of upstream discussion.

## Additional Notes

This slice intentionally does not change request module names, request payloads, retry policy, retry-exhausted `None` handling, page-ID acquisition, cached revision reuse, duplicate page-ID cloning, source/html clone preservation, revision row parsing, user/date parsing, comment spacing, lazy revision reads, or live Wikidot behavior. It only converts missing batched revision-list response `body` fields into site/page/id-context `NoElementException` failures before parser work.
