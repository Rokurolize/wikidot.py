# PR Draft: Validate Direct Page File Response Bodies

## Summary

`PageFileCollection.acquire(page)` retrieves the generated `files/PageFilesModule` response for a single page and parses the attached-file table. Earlier local slices made direct page-file reads retry-aware, cache-aware, page-context-rich, parser-scoped, filename-spacing-preserving, and consistent with collection-level file-list acquisition. The remaining malformed response-body path still read `response.json()["body"]`, so an AMC response without a `body` field leaked a raw `KeyError` before the parser could report which site and page produced the malformed file-list response.

This follow-up keeps cached direct acquisition, `files/PageFilesModule` request payloads, retry-exhausted `None` handling, successful file parsing, valid empty file-list responses, direct row scoping, nested row rejection, absolute URL preservation, MIME parsing, filename spacing, size parsing, lazy `Page.files`, and collection-level page file batching unchanged. It only treats a direct page-file response without a JSON `body` field as a malformed file-list response and raises `NoElementException` with site and page context before BeautifulSoup parsing or file parsing.

## Related Issue

Builds on [039-pr-page-files-exhausted-retry-error.md](039-pr-page-files-exhausted-retry-error.md), [041-pr-retry-direct-page-file-acquire.md](041-pr-retry-direct-page-file-acquire.md), [064-pr-deduplicate-page-file-fetches.md](064-pr-deduplicate-page-file-fetches.md), [075-pr-reuse-page-file-list-parsing.md](075-pr-reuse-page-file-list-parsing.md), [095-pr-scope-page-file-row-parsing.md](095-pr-scope-page-file-row-parsing.md), [117-pr-preserve-page-file-name-spacing.md](117-pr-preserve-page-file-name-spacing.md), [130-pr-reuse-cached-duplicate-page-files.md](130-pr-reuse-cached-duplicate-page-files.md), [144-pr-skip-cached-direct-page-files.md](144-pr-skip-cached-direct-page-files.md), [151-pr-page-file-failure-context.md](151-pr-page-file-failure-context.md), [181-pr-page-file-direct-fetch-context.md](181-pr-page-file-direct-fetch-context.md), and [193-pr-page-file-direct-fetch-site-context.md](193-pr-page-file-direct-fetch-site-context.md). Those drafts established page-file acquisition as a practical retry-aware workflow with cache behavior, parser boundaries, duplicate handling, text preservation, and site/page diagnostics.

No upstream issue was filed from this local workspace.

## Changes

- Read the direct file-list response body with `response.json().get("body")`.
- Convert a missing direct page-file response `body` field into `NoElementException` with site and page context.
- Preserve retry-exhausted `None` response handling as `UnexpectedException`.
- Preserve successful file-list parsing, valid empty-file responses, cached direct acquisition, request payloads, direct row scoping, nested row rejection, absolute URL preservation, MIME parsing, filename spacing, size parsing, lazy `Page.files`, and collection-level page file batching.
- Add a focused regression for missing direct page-file response-body handling through public `PageFileCollection.acquire(page)`.

## Type Of Change

- Bug fix / diagnostics improvement
- Page file response validation
- Test coverage

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| A direct page-file response without JSON `body` still fails before HTML parsing or file parsing. | `TestPageFileCollectionAcquire.test_acquire_missing_response_body_includes_page_context` returns `{}` from the direct AMC response and expects `NoElementException`. | A change that raises raw `KeyError`, silently returns an empty file collection, or enters file parsing rejects this local completion claim. |
| Malformed direct page-file response errors identify site and page. | The focused regression asserts `Page file list response body is not found for site: test-site, page: test-page`. | A generic parser exception without site/page context rejects this local completion claim. |
| Retry-exhausted `None` direct page-file responses remain distinct from malformed JSON body responses. | `TestPageFileCollectionAcquire.test_acquire_raises_when_retry_is_exhausted` remains green and expects `UnexpectedException`. | A change that turns skipped/exhausted `None` responses into body-validation failures rejects this local completion claim. |
| Existing direct page-file behavior remains green. | `uv run pytest tests/unit/test_page_file.py -q` passed 30 tests. | Regressions in cached direct acquisition, request payloads, successful parsing, invalid row handling, nested row filtering, filename spacing, absolute URL preservation, MIME parsing, size parsing, or empty file-list handling reject this local completion claim. |
| Adjacent page workflows remain green. | `uv run pytest tests/unit/test_page_file.py tests/unit/test_page.py -q` passed 146 tests. | Regressions in lazy `Page.files`, collection-level page file acquisition, page source/revision/vote flows, page lookup, or page mutation boundaries reject this local completion claim. |
| Broad unit and static quality gates remain green. | `uv run pytest tests/unit -q`; `uv run ruff format src tests`; `uv run ruff check src tests`; `uv run ruff format --check src tests`; `uv run mypy src tests`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject this local completion claim. |

## Testing

Implemented locally in commit `9d01b97 fix(page_file): validate file response bodies`.

- RED: `uv run pytest tests/unit/test_page_file.py::TestPageFileCollectionAcquire::test_acquire_missing_response_body_includes_page_context -q` failed before the fix with `KeyError: 'body'`.
- GREEN: `uv run pytest tests/unit/test_page_file.py::TestPageFileCollectionAcquire::test_acquire_missing_response_body_includes_page_context tests/unit/test_page_file.py::TestPageFileCollectionAcquire::test_acquire_raises_when_retry_is_exhausted tests/unit/test_page_file.py::TestPageFileCollectionAcquire::test_acquire_success -q` passed 3 tests.
- `uv run pytest tests/unit/test_page_file.py -q` passed 30 tests.
- `uv run pytest tests/unit/test_page_file.py tests/unit/test_page.py -q` passed 146 tests.
- `uv run pytest tests/unit -q` passed 753 tests.
- `uv run ruff format src tests` left 80 files unchanged.
- `uv run ruff check src tests`.
- `uv run ruff format --check src tests`.
- `uv run mypy src tests`.
- `git diff --check`.

Not run successfully: `pyright --version` because this environment could not find a `pyright` executable.

## Acceptance Criteria

- `PageFileCollection.acquire(page)` still uses retry-aware AMC and the same `files/PageFilesModule` request payload.
- A missing direct page-file response JSON `body` raises `NoElementException` naming the site and page.
- Missing response-body handling does not convert retry-exhausted `None` responses into malformed-body failures.
- Cached direct acquisition still returns an existing `PageFileCollection` without an AMC request.
- Successful file-list parsing, valid empty-file responses, direct row scoping, nested row rejection, absolute URL preservation, MIME extraction, filename spacing, size parsing, lazy `Page.files`, and collection-level page file batching remain unchanged.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Attached-file inspection depends on Wikidot returning a JSON `body` field for the generated file-list module response. If that field is missing, wikidot.py should report a structured malformed-response failure with the site and page, not a raw dictionary `KeyError`, so caller logs can route the failure without preserving raw response JSON, generated file-list HTML, credentials, local rollout paths, or private attachment metadata.

## Local Evidence, Not For Upstream Paste

- Earlier local drafts established page-file acquisition as retry-aware, parser-scoped, cache-aware, duplicate-aware, and used through both direct `PageFileCollection.acquire(page)` and lazy `Page.files` / collection-level file helpers.
- Recent response-body validation slices in private-message, forum-post, forum-category, forum-thread, site-application, and site-member modules showed the same raw `KeyError` failure mode at AMC response-body boundaries.
- The refreshed complexity memo continues to list raw response-body boundaries in `page_revision`, `forum_post_revision`, `page`, and `site` as follow-up leads, but this slice only claims direct page-file response-body validation.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, raw response JSON, generated file-list HTML, and private attachment data out of upstream discussion.

## Additional Notes

This slice intentionally does not change request module names, request payloads, retry policy, retry-exhausted `None` handling, direct cache behavior, file-list parser selectors, URL normalization, file size parsing, `Page.files`, collection-level page file batching, mutation methods, or live Wikidot behavior. It only converts missing direct page-file response `body` fields into site/page-context `NoElementException` failures before parser work.
