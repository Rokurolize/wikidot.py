# PR Draft: Include Page Context In Direct Page File Fetch Failures

## Summary

`PageFileCollection.acquire(page)` is the public direct helper for reading a single page's attached-file list. Earlier local slices made that helper retry-aware and made `Page.files` include the page fullname when lazy file-list acquisition failed, but the direct helper still raised `UnexpectedException("Cannot retrieve page files")` when retry exhaustion returned `None`.

This follow-up keeps retry-aware direct file-list acquisition, cached direct acquisition, parser behavior, URL normalization, size parsing, empty file-list behavior, and exception type unchanged, but includes the page fullname in direct exhausted-retry failures: `Cannot retrieve page files: <fullname>`.

## Related Issue

Builds on [039-pr-page-files-exhausted-retry-error.md](039-pr-page-files-exhausted-retry-error.md), [041-pr-retry-direct-page-file-acquire.md](041-pr-retry-direct-page-file-acquire.md), [064-pr-deduplicate-page-file-fetches.md](064-pr-deduplicate-page-file-fetches.md), [075-pr-reuse-page-file-list-parsing.md](075-pr-reuse-page-file-list-parsing.md), [095-pr-scope-page-file-row-parsing.md](095-pr-scope-page-file-row-parsing.md), [117-pr-preserve-page-file-name-spacing.md](117-pr-preserve-page-file-name-spacing.md), [144-pr-skip-cached-direct-page-files.md](144-pr-skip-cached-direct-page-files.md), and [151-pr-page-file-failure-context.md](151-pr-page-file-failure-context.md), because those drafts established page file-list retry behavior, duplicate/cached behavior, parser scoping, filename spacing, direct cache behavior, and page-context lazy file failures.

No upstream issue was filed from this local workspace.

## Changes

- Include page fullname when `PageFileCollection.acquire(page)` exhausts retry-aware direct file-list fetching.
- Tighten the existing direct exhausted-retry regression to assert page context.
- Preserve cached direct acquisition, `files/PageFilesModule` request payloads, retry policy, file-list parser behavior, empty file-list responses, URL normalization, MIME parsing, size parsing, and exception type.

## Type Of Change

- Bug fix / diagnostics improvement
- Direct page file-list fetch failure context
- Test tightening

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| Direct page-file acquisition still fails explicitly when retry is exhausted. | `TestPageFileCollectionAcquire.test_acquire_raises_when_retry_is_exhausted` returns `(None,)` from retry fetches and expects `UnexpectedException`. | Returning an empty `PageFileCollection`, parsing a missing response, or calling plain `amc_request(...)` rejects this local completion claim. |
| Direct page-file failures identify the affected page. | The focused regression asserts `Cannot retrieve page files: test-page`. | The RED test failed before the fix because the message was only `Cannot retrieve page files`. |
| Direct page-file behavior remains green. | `uv run pytest tests/unit/test_page_file.py -q` passed 29 tests. | Regressions in cached direct acquisition, successful parsing, invalid row handling, filename spacing, URL normalization, size parsing, or empty file-list handling reject this local completion claim. |
| Broad unit and static quality gates remain green. | `uv run pytest tests/unit -q`; `uv run ruff check src tests`; `uv run ruff format --check src tests`; `uv run mypy src tests`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject this local completion claim. |

## Testing

Implemented locally in commit `6479c6d fix(page_file): include page in direct fetch failures`.

- RED: `uv run pytest tests/unit/test_page_file.py::TestPageFileCollectionAcquire::test_acquire_raises_when_retry_is_exhausted -q` failed before the fix because the message only said `Cannot retrieve page files`.
- GREEN: `uv run pytest tests/unit/test_page_file.py::TestPageFileCollectionAcquire::test_acquire_raises_when_retry_is_exhausted -q`
- `uv run pytest tests/unit/test_page_file.py -q` passed 29 tests.
- `uv run pytest tests/unit -q` passed 725 tests.
- `uv run ruff check src tests`
- `uv run ruff format --check src tests`
- `uv run mypy src tests`
- `git diff --check`

Not run successfully: `pyright` because this environment could not find a `pyright` executable.

## Acceptance Criteria

- `PageFileCollection.acquire(page)` still uses retry-aware AMC, not plain `amc_request(...)`.
- `PageFileCollection.acquire(page)` still raises `UnexpectedException` when the retry helper returns `None`.
- The direct exhausted-retry failure names the page fullname.
- Cached direct acquisition still returns an existing `PageFileCollection` without an AMC request.
- Successful file-list acquisition, empty-file responses, parser row filtering, URL normalization, MIME parsing, size parsing, and `Page.files` behavior remain unchanged.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Attached-file inspection is a common read path for asset audits, publication verification, and download reconciliation. When direct file-list fetching exhausts retry, logs should identify the affected page so callers can diagnose the missing attachment list without keeping raw response HTML, credentials, local rollout paths, or page contents.

## Local Evidence, Not For Upstream Paste

- Earlier local drafts repeatedly identified page file-list reads as a practical workflow surface: retry-aware direct acquisition, lazy `Page.files` failure visibility, duplicate file-list request reduction, parse reuse, row scoping, filename spacing, cached duplicate reuse, and cached direct acquisition.
- Recent context slices showed that compact page/object identifiers improve resumable ledgers without changing successful behavior.
- This slice only claims direct page-file fetch failure diagnostics. It does not claim any live Wikidot behavior change.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, raw response HTML, and saved page contents out of upstream discussion.

## Additional Notes

This slice intentionally does not change request module names, retry policy, cached direct acquisition, file parser selectors, URL normalization, file size parsing, `Page.files`, collection-level page file batching, mutation methods, or live Wikidot behavior. It only adds page fullname context to an existing direct exhausted-retry failure.
