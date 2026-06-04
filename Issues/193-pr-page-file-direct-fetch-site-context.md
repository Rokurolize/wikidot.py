# PR Draft: Include Site Context In Direct Page File Fetch Failures

## Summary

`PageFileCollection.acquire(page)` is the public direct helper for reading a single page's attached-file list. Earlier local slices made that helper retry-aware and added the page fullname to exhausted retry failures, but multi-site crawler and publishing workflows can inspect the same page fullname across different Wikidot sites. A page-only message such as `Cannot retrieve page files: scp-001` is still ambiguous in those logs.

This follow-up keeps retry-aware direct file-list acquisition, cached direct acquisition, parser behavior, URL normalization, MIME parsing, size parsing, empty file-list behavior, and exception type unchanged. It only adds the site unix name to the direct exhausted-retry failure message: `Cannot retrieve page files for site: <site>, page: <fullname>`.

## Related Issue

Builds on [041-pr-retry-direct-page-file-acquire.md](041-pr-retry-direct-page-file-acquire.md), [144-pr-skip-cached-direct-page-files.md](144-pr-skip-cached-direct-page-files.md), [151-pr-page-file-failure-context.md](151-pr-page-file-failure-context.md), [181-pr-page-file-direct-fetch-context.md](181-pr-page-file-direct-fetch-context.md), and [192-pr-page-auxiliary-fetch-site-context.md](192-pr-page-auxiliary-fetch-site-context.md). Those drafts established retry-aware direct page-file reads, cached direct acquisition, page-context lazy and direct file failures, and site-context auxiliary page fetch failures as practical local improvement surfaces.

No upstream issue was filed from this local workspace.

## Changes

- Include `page.site.unix_name` and page fullname when `PageFileCollection.acquire(page)` cannot retrieve `files/PageFilesModule` after retries.
- Tighten the existing direct exhausted-retry regression to assert site/page context.
- Preserve cached direct acquisition, `files/PageFilesModule` request payloads, retry policy, file-list parser behavior, empty-file responses, URL normalization, MIME parsing, size parsing, and exception type.

## Type Of Change

- Bug fix / diagnostics improvement
- Direct page file-list fetch failure context
- Test expectation strengthening

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| Direct page-file acquisition still fails explicitly when retry is exhausted. | `TestPageFileCollectionAcquire.test_acquire_raises_when_retry_is_exhausted` returns `(None,)` from retry fetches and expects `UnexpectedException`. | Returning an empty `PageFileCollection`, parsing a missing response, or calling plain `amc_request(...)` rejects this local completion claim. |
| Direct page-file failures identify both site and page. | The focused regression asserts `Cannot retrieve page files for site: test-site, page: test-page`. | The RED test failed before the fix because the message only said `Cannot retrieve page files: test-page`. |
| Direct page-file behavior remains green. | `uv run pytest tests/unit/test_page_file.py -q` passed 29 tests; `uv run pytest tests/unit/test_page.py tests/unit/test_page_file.py -q` passed 143 tests. | Regressions in cached direct acquisition, successful parsing, invalid row handling, filename spacing, URL normalization, size parsing, empty file-list handling, or lazy `Page.files` behavior reject this local completion claim. |
| Broad unit and static quality gates remain green. | `uv run pytest tests/unit -q`; `uv run ruff check src tests`; `uv run ruff format --check src tests`; `uv run mypy src tests`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject this local completion claim. |

## Testing

Implemented locally in commit `7bcff98 fix(page_file): include site in direct fetch failures`.

- RED: `uv run pytest tests/unit/test_page_file.py::TestPageFileCollectionAcquire::test_acquire_raises_when_retry_is_exhausted -q` failed before the fix because the exception message was `Cannot retrieve page files: test-page`.
- GREEN: `uv run pytest tests/unit/test_page_file.py::TestPageFileCollectionAcquire::test_acquire_raises_when_retry_is_exhausted -q`.
- `uv run pytest tests/unit/test_page_file.py -q` passed 29 tests.
- `uv run pytest tests/unit/test_page.py tests/unit/test_page_file.py -q` passed 143 tests.
- `uv run pytest tests/unit -q` passed 733 tests.
- `uv run ruff check src tests`.
- `uv run ruff format --check src tests`.
- `uv run mypy src tests`.
- `git diff --check`.

Not run successfully: `pyright --version` because this environment could not find a `pyright` executable.

## Acceptance Criteria

- `PageFileCollection.acquire(page)` still returns a cached `PageFileCollection` without an AMC request when `page._files` is already populated.
- `PageFileCollection.acquire(page)` still requests `files/PageFilesModule` with the current page ID through retry-aware AMC.
- `PageFileCollection.acquire(page)` still raises `UnexpectedException` when the retry helper returns `None`.
- The direct exhausted-retry failure now names both site unix name and page fullname.
- Successful file-list acquisition, empty-file responses, parser row filtering, URL normalization, MIME parsing, size parsing, and lazy `Page.files` behavior remain unchanged.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Attached-file inspection is a common read path for asset audits, publication verification, and download reconciliation. When direct file-list fetching exhausts retry, logs should identify both the site and page without requiring raw response bodies, account context, local rollout paths, or saved page contents. This keeps the existing strict failure behavior while making multi-site failure routing easier.

## Local Evidence, Not For Upstream Paste

- Earlier local drafts repeatedly identified page file-list reads as a practical workflow surface: retry-aware direct acquisition, lazy `Page.files` failure visibility, duplicate file-list request reduction, parse reuse, row scoping, filename spacing, cached duplicate reuse, cached direct acquisition, and page-context direct fetch failures.
- Recent context slices showed that compact site/object identifiers improve resumable ledgers without changing successful behavior.
- This slice only claims direct page-file fetch failure diagnostics. It does not claim any live Wikidot behavior change.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, raw response HTML, and saved page contents out of upstream discussion.

## Additional Notes

This slice intentionally does not change request module names, retry policy, cached direct acquisition, file parser selectors, URL normalization, file size parsing, `Page.files`, collection-level page file batching, mutation methods, or live Wikidot behavior. It only adds site unix name context to an existing direct exhausted-retry failure.
