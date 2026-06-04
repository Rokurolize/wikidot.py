# PR Draft: Validate Batched Page File Response Bodies

## Summary

`PageCollection.get_page_files()` batches `files--/FilesModule` requests for pages whose file data is still uncached, reuses cached duplicate page-ID file collections, and parses the returned file table into page-owned `PageFileCollection` objects. The remaining malformed response-body path still read `response.json()["body"]`, so an AMC response without a `body` field leaked a raw `KeyError` before the file boundary could report which site and page produced the malformed response.

This follow-up keeps page-ID acquisition, cached file reuse, duplicate page-ID cloning, request payloads, retry-exhausted `None` skip behavior, file row parsing, file URL construction, and lazy `Page.files` behavior unchanged. It only treats batched file responses without JSON `body` fields as malformed file responses and raises `NoElementException` with site, page, and page ID context before BeautifulSoup parsing.

## Related Issue

Builds on [004-pr-batched-revision-vote-file-fetch.md](004-pr-batched-revision-vote-file-fetch.md), [095-pr-scope-page-file-row-parsing.md](095-pr-scope-page-file-row-parsing.md), [130-pr-reuse-cached-duplicate-page-files.md](130-pr-reuse-cached-duplicate-page-files.md), [215-pr-page-file-response-body-context.md](215-pr-page-file-response-body-context.md), and [223-pr-page-vote-batch-response-body-context.md](223-pr-page-vote-batch-response-body-context.md). Those drafts established page file collection reads as cached, duplicate-aware workflows with scoped file parsing and site/page diagnostics.

No upstream issue was filed from this local workspace.

## Changes

- Read batched page file response bodies with `response.json().get("body")`.
- Convert missing `files--/FilesModule` response `body` fields into `NoElementException` with site, page, and page ID context.
- Preserve retry-exhausted `None` responses as skipped entries.
- Preserve cached file reuse, duplicate page-ID cloning, file row parsing, file URL construction, and lazy files behavior.
- Add a focused regression for missing batched file response bodies through public `PageCollection.get_page_files()`.

## Type Of Change

- Bug fix / diagnostics improvement
- Page file batch response validation
- Test coverage

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| A batched page file response without JSON `body` fails before BeautifulSoup parsing. | `TestPageCollectionAcquire.test_acquire_files_missing_response_body_includes_site_page_context` returns `{}` from the file response and expects `NoElementException`. | A change that raises raw `KeyError`, fabricates an empty file collection, or enters file parsing rejects this local completion claim. |
| Malformed file response errors identify site, page, and page ID. | The focused regression asserts `Page file response body is not found for site: test-site, page: test-page (id=...)`. | An exception without site/page/id context rejects this local completion claim. |
| Missing-body failure does not populate files. | The focused regression verifies `mock_page_with_id._files is None` after the malformed response. | A change that stores an empty or partial file collection rejects this local completion claim. |
| Retry-exhausted `None` responses remain distinct from malformed response bodies. | Existing lazy retry-exhausted files tests and collection acquisition tests remain green. | A change that turns retry exhaustion into body-validation failure rejects this local completion claim. |
| Existing collection acquisition behavior remains green. | `uv run pytest tests/unit/test_page.py::TestPageCollectionAcquire -q` passed 38 tests. | Regressions in page ID acquisition, source acquisition, revision acquisition, vote acquisition, file duplicate reuse, or file parser context reject this local completion claim. |
| Page and adjacent site workflows remain green. | `uv run pytest tests/unit/test_page.py -q` passed 124 tests; `uv run pytest tests/unit/test_page.py tests/unit/test_page_file.py tests/unit/test_page_revision.py tests/unit/test_page_votes.py tests/unit/test_site.py -q` passed 271 tests. | Regressions in page source/revision/vote/file/site flows reject this local completion claim. |
| Broad unit and static quality gates remain green. | `uv run pytest tests/unit -q`; `uv run ruff format src tests`; `uv run ruff check src tests`; `uv run ruff format --check src tests`; `uv run mypy src tests`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject this local completion claim. |

## Testing

Implemented locally in commit `7e90d3f fix(page): validate batched file response bodies`.

- RED: `uv run pytest tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_files_missing_response_body_includes_site_page_context -q` failed before the fix with `KeyError: 'body'`.
- GREEN: `uv run pytest tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_files_missing_response_body_includes_site_page_context -q` passed after the fix.
- `uv run pytest tests/unit/test_page.py::TestPageCollectionAcquire -q` passed 38 tests.
- `uv run pytest tests/unit/test_page.py -q` passed 124 tests.
- `uv run pytest tests/unit/test_page.py tests/unit/test_page_file.py tests/unit/test_page_revision.py tests/unit/test_page_votes.py tests/unit/test_site.py -q` passed 271 tests.
- `uv run pytest tests/unit -q` passed 767 tests.
- `uv run ruff format src tests` left 80 files unchanged.
- `uv run ruff check src tests`.
- `uv run ruff format --check src tests`.
- `uv run mypy src tests`.
- `git diff --check`.

Not run successfully: `pyright --version` because this environment could not find a `pyright` executable.

## Acceptance Criteria

- `PageCollection.get_page_files()` still batches uncached page file requests by page ID.
- Cached file reuse, duplicate page-ID cloning, file row parsing, file URL construction, and lazy file reads remain unchanged.
- Missing batched file response JSON `body` raises `NoElementException` naming the site, page, and page ID.
- Missing response-body handling does not convert retry-exhausted `None` responses into malformed-body failures.
- Malformed missing-body responses do not populate page files.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, non-goals, verification, and false-positive rejection checks.
- `Issues/README.md` records the local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

Batched page file acquisition is a common file inventory read path. If Wikidot returns a malformed generated-module response, wikidot.py should report a structured site/page/id failure, not a raw dictionary `KeyError`, so caller logs can route the failure without preserving raw response JSON, generated file-list HTML, credentials, or private site content.

## Local Evidence, Not For Upstream Paste

- Earlier local drafts established page file collection batching, duplicate file clone behavior, direct page file fetch diagnostics, and scoped file row parsing.
- Recent response-body validation slices across private-message, forum-post, forum-category, forum-thread, site-application, site-member, direct page-file, page-revision source/HTML, forum-post-revision, recent-changes, page auxiliary, ListPages, batched page source, batched page revision-list, and batched page vote modules showed the same raw `KeyError` failure mode at AMC response-body boundaries.
- The refreshed complexity memo should no longer list direct `response.json()["body"]` boundaries inside `src/wikidot/module/page.py` after this slice removes the final page collection batch helper raw body read.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, raw response JSON, generated file-list HTML, file names, file URLs, and site content out of upstream discussion.

## Additional Notes

This slice intentionally does not change request module names, request payloads, retry policy, retry-exhausted `None` handling, page-ID acquisition, cached file reuse, duplicate page-ID cloning, file row parsing, file URL construction, lazy file reads, or live Wikidot behavior. It only converts missing batched file response `body` fields into site/page/id-context `NoElementException` failures before parser work.
