# PR Draft: Include Page Context In Direct File Failures

## Summary

`Page.files` is the direct single-page file-list path used by callers that inspect page attachments before downloading, auditing, or reconciling page assets. When retry-aware acquisition exhausted without populating `_files`, the property raised `NotFoundException("Cannot find page files")`, which hid the affected page name in plain-text logs.

This follow-up keeps the existing exception type and acquisition behavior, but includes `page.fullname` in the failure message: `Cannot find page files: <fullname>`. The change aligns direct file-list failures with the page-context direction already used by source collection failures, direct source reads, and direct revision-list reads.

## Related Issue

Builds on [039-pr-page-files-exhausted-retry-error.md](039-pr-page-files-exhausted-retry-error.md), [041-pr-retry-direct-page-file-acquire.md](041-pr-retry-direct-page-file-acquire.md), [064-pr-deduplicate-page-file-fetches.md](064-pr-deduplicate-page-file-fetches.md), [075-pr-reuse-page-file-list-parsing.md](075-pr-reuse-page-file-list-parsing.md), [095-pr-scope-page-file-row-parsing.md](095-pr-scope-page-file-row-parsing.md), [117-pr-preserve-page-file-name-spacing.md](117-pr-preserve-page-file-name-spacing.md), [130-pr-reuse-cached-duplicate-page-files.md](130-pr-reuse-cached-duplicate-page-files.md), [144-pr-skip-cached-direct-page-files.md](144-pr-skip-cached-direct-page-files.md), [149-pr-page-source-failure-context.md](149-pr-page-source-failure-context.md), and [150-pr-page-revision-failure-context.md](150-pr-page-revision-failure-context.md).

No upstream issue was filed from this local workspace.

## Changes

- Make `Page.files` include `self.fullname` when automatic file-list acquisition leaves `_files` unset.
- Update the focused direct file-list exhausted-retry test to assert the page-context message.
- Preserve file request construction, retry behavior, file-list parsing, empty-file success semantics, cache behavior, duplicate-page handling, and direct file acquisition behavior.

## Type Of Change

- Bug fix / diagnostics improvement
- File-list error-context ergonomics
- Test addition/modification

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| Lazy single-page file-list failures identify the affected page. | `TestPageProperties.test_files_property_includes_page_context_when_retry_is_exhausted` asserts `Cannot find page files: test-page` after `amc_request_with_retry(...)` returns `None`. | The RED test failed before the fix because the exception message was only `Cannot find page files`. |
| File-list acquisition behavior remains unchanged. | The focused test also asserts the same `files/PageFilesModule` request body, `amc_request(...)` is not called, and `_files` remains `None`. | A change that alters request construction, retry use, cache population, or exhausted-retry state rejects this local completion claim. |
| Adjacent page and page-file behavior remains green. | `uv run --extra test pytest tests/unit/test_page.py tests/unit/test_page_file.py -q` passed 136 tests. | Regressions in page file parsing, empty file-list handling, duplicate response reuse, direct file acquisition, or page property behavior reject this local completion claim. |
| Broad unit and static quality gates remain green. | `uv run pytest tests/unit -q`; `uv run ruff check`; `uv run ruff format --check`; `uv run mypy src tests --install-types --non-interactive`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject this local completion claim. |

## Testing

Implemented locally in commit `7eb1a4e fix(page): include page name in file failures`.

- RED: `uv run --extra test pytest tests/unit/test_page.py::TestPageProperties::test_files_property_includes_page_context_when_retry_is_exhausted -q` failed before the fix because `Page.files` raised `Cannot find page files` without the page fullname.
- GREEN: `uv run --extra test pytest tests/unit/test_page.py::TestPageProperties::test_files_property_includes_page_context_when_retry_is_exhausted -q`
- `uv run --extra test pytest tests/unit/test_page.py tests/unit/test_page_file.py -q` passed 136 tests.
- `uv run pytest tests/unit -q` passed 713 tests.
- `uv run ruff check`
- `uv run ruff format --check`
- `uv run mypy src tests --install-types --non-interactive`
- `git diff --check`

Not run: `uv run pyright` because this environment could not find a `pyright` executable.

## Acceptance Criteria

- `Page.files` still performs lazy retry-aware file-list acquisition through `PageCollection(...).get_page_files()`.
- If lazy acquisition does not populate `_files`, `Page.files` raises `NotFoundException("Cannot find page files: <fullname>")`.
- Successful file-list acquisition, empty-file responses, `PageFileCollection` ownership, duplicate-page response reuse, and direct file acquisition remain unchanged.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

File-list failures often appear in asset audit and page export logs where the file collection itself is unavailable. The exception should identify the affected page without requiring callers to reconstruct the `Page` object from surrounding state, especially because adjacent direct source and revision failure paths already provide this context.

## Local Evidence, Not For Upstream Paste

- Local rollout-backed drafts already needed visible retry-exhaustion failures for page files, direct file acquisition, duplicate file-list reuse, and direct cached file fetches.
- Recent source and revision failure work showed that page-context messages make plain-text logs and resumable ledgers easier to triage without inspecting raw objects.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, and saved page contents out of upstream discussion.

## Additional Notes

This slice intentionally does not change `Page.source`, `Page.revisions`, `Page.votes`, `PageFileCollection.acquire()`, file parsing, mutation methods, or live Wikidot behavior. Similar direct property context improvements remain plausible follow-up slices.
