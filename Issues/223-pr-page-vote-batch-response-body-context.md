# PR Draft: Validate Batched Page Vote Response Bodies

## Summary

`PageCollection.get_page_votes()` batches `pagerate/WhoRatedPageModule` requests for pages whose vote data is still uncached, reuses cached duplicate page-ID vote collections, and parses the WhoRated markup into page-owned `PageVoteCollection` objects. The remaining malformed response-body path still read `response.json()["body"]`, so an AMC response without a `body` field leaked a raw `KeyError` before the vote boundary could report which site and page produced the malformed response.

This follow-up keeps page-ID acquisition, cached vote reuse, duplicate page-ID cloning, request payloads, retry-exhausted `None` skip behavior, vote container discovery, non-vote span filtering, user/value count mismatch diagnostics, user parsing, vote value parsing, and lazy `Page.votes` behavior unchanged. It only treats batched vote responses without JSON `body` fields as malformed vote responses and raises `NoElementException` with site, page, and page ID context before BeautifulSoup parsing.

## Related Issue

Builds on [004-pr-batched-revision-vote-file-fetch.md](004-pr-batched-revision-vote-file-fetch.md), [106-pr-page-vote-mismatch-site-context.md](106-pr-page-vote-mismatch-site-context.md), [112-pr-page-vote-row-scope.md](112-pr-page-vote-row-scope.md), and [222-pr-page-revision-batch-response-body-context.md](222-pr-page-revision-batch-response-body-context.md). Those drafts established page vote collection reads as cached, duplicate-aware workflows with scoped vote parsing and site/page diagnostics.

No upstream issue was filed from this local workspace.

## Changes

- Read batched page vote response bodies with `response.json().get("body")`.
- Convert missing `pagerate/WhoRatedPageModule` response `body` fields into `NoElementException` with site, page, and page ID context.
- Preserve retry-exhausted `None` responses as skipped entries.
- Preserve cached vote reuse, duplicate page-ID cloning, vote container discovery, non-vote span filtering, user/value mismatch diagnostics, user parsing, vote value parsing, and lazy votes behavior.
- Add a focused regression for missing batched vote response bodies through public `PageCollection.get_page_votes()`.

## Type Of Change

- Bug fix / diagnostics improvement
- Page vote batch response validation
- Test coverage

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| A batched page vote response without JSON `body` fails before BeautifulSoup parsing. | `TestPageCollectionAcquire.test_acquire_votes_missing_response_body_includes_site_page_context` returns `{}` from the vote response and expects `NoElementException`. | A change that raises raw `KeyError`, fabricates an empty vote collection, or enters vote parsing rejects this local completion claim. |
| Malformed vote response errors identify site, page, and page ID. | The focused regression asserts `Page vote response body is not found for site: test-site, page: test-page (id=...)`. | An exception without site/page/id context rejects this local completion claim. |
| Missing-body failure does not populate votes. | The focused regression verifies `mock_page_with_id._votes is None` after the malformed response. | A change that stores an empty or partial vote collection rejects this local completion claim. |
| Retry-exhausted `None` responses remain distinct from malformed response bodies. | Existing lazy retry-exhausted votes tests and collection acquisition tests remain green. | A change that turns retry exhaustion into body-validation failure rejects this local completion claim. |
| Existing collection acquisition behavior remains green. | `uv run pytest tests/unit/test_page.py::TestPageCollectionAcquire -q` passed 37 tests. | Regressions in page ID acquisition, source acquisition, revision acquisition, vote duplicate reuse, file acquisition, or vote parser context reject this local completion claim. |
| Page and adjacent site workflows remain green. | `uv run pytest tests/unit/test_page.py -q` passed 123 tests; `uv run pytest tests/unit/test_page.py tests/unit/test_page_file.py tests/unit/test_page_revision.py tests/unit/test_page_votes.py tests/unit/test_site.py -q` passed 270 tests. | Regressions in page source/revision/vote/file/site flows reject this local completion claim. |
| Broad unit and static quality gates remain green. | `uv run pytest tests/unit -q`; `uv run ruff format src tests`; `uv run ruff check src tests`; `uv run ruff format --check src tests`; `uv run mypy src tests`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject this local completion claim. |

## Testing

Implemented locally in commit `91111ec fix(page): validate batched vote response bodies`.

- RED: `uv run pytest tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_votes_missing_response_body_includes_site_page_context -q` failed before the fix with `KeyError: 'body'`.
- GREEN: `uv run pytest tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_votes_missing_response_body_includes_site_page_context -q` passed after the fix.
- `uv run pytest tests/unit/test_page.py::TestPageCollectionAcquire -q` passed 37 tests.
- `uv run pytest tests/unit/test_page.py -q` passed 123 tests.
- `uv run pytest tests/unit/test_page.py tests/unit/test_page_file.py tests/unit/test_page_revision.py tests/unit/test_page_votes.py tests/unit/test_site.py -q` passed 270 tests.
- `uv run pytest tests/unit -q` passed 766 tests.
- `uv run ruff format src tests` left 80 files unchanged.
- `uv run ruff check src tests`.
- `uv run ruff format --check src tests`.
- `uv run mypy src tests`.
- `git diff --check`.

Not run successfully: `pyright --version` because this environment could not find a `pyright` executable.

## Acceptance Criteria

- `PageCollection.get_page_votes()` still batches uncached page vote requests by page ID.
- Cached vote reuse, duplicate page-ID cloning, vote container discovery, non-vote span filtering, user/value mismatch diagnostics, user parsing, and vote value parsing remain unchanged.
- Missing batched vote response JSON `body` raises `NoElementException` naming the site, page, and page ID.
- Missing response-body handling does not convert retry-exhausted `None` responses into malformed-body failures.
- Malformed missing-body responses do not populate page votes.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, non-goals, verification, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and the local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

Batched page vote acquisition is a common rating read path. If Wikidot returns a malformed generated-module response, wikidot.py should report a structured site/page/id failure, not a raw dictionary `KeyError`, so caller logs can route the failure without preserving raw response JSON, generated WhoRated HTML, user names, credentials, or private site content.

## Local Evidence, Not For Upstream Paste

- Earlier local drafts established page vote collection batching, duplicate vote clone behavior, vote mismatch diagnostics, and scoped vote parsing.
- Recent response-body validation slices across private-message, forum-post, forum-category, forum-thread, site-application, site-member, page-file, page-revision source/HTML, forum-post-revision, recent-changes, page auxiliary, ListPages, batched page source, and batched page revision-list modules showed the same raw `KeyError` failure mode at AMC response-body boundaries.
- The refreshed complexity memo continues to list the raw response-body boundary in the page collection file batch helper as a follow-up lead after this slice removes the direct batched vote raw body read.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, raw response JSON, generated WhoRated HTML, user names, vote data, and site content out of upstream discussion.

## Additional Notes

This slice intentionally does not change request module names, request payloads, retry policy, retry-exhausted `None` handling, page-ID acquisition, cached vote reuse, duplicate page-ID cloning, vote container discovery, non-vote span filtering, user/value mismatch diagnostics, user parsing, vote value parsing, lazy vote reads, or live Wikidot behavior. It only converts missing batched vote response `body` fields into site/page/id-context `NoElementException` failures before parser work.
