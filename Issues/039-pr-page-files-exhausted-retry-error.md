# PR Draft: Surface Failed Page File Fetches

## Summary

`Page.files` automatically calls `PageCollection(...).get_page_files()` when the attached-file list has not been loaded. The collection-level retry path intentionally leaves `page._files` as `None` when a page's `files/PageFilesModule` request exhausts retries, so callers can distinguish a failed fetch from a successful response with no attached files.

The property layer erased that distinction by fabricating an empty `PageFileCollection` whenever `_files` was still `None`. A transient or exhausted file-list failure could therefore look identical to a real "no files" page.

The fix removes the fallback and raises `NotFoundException("Cannot find page files")` when acquisition leaves `_files` unset. A successful empty file-list response still returns an empty `PageFileCollection`.

## Related Issue

Complements [010-pr-retry-batched-file-fetches.md](010-pr-retry-batched-file-fetches.md), which made batched file fetches retry-aware and preserved failed pages as not acquired. Also aligns with [009-pr-skip-cached-page-detail-fetches.md](009-pr-skip-cached-page-detail-fetches.md), which treats cached detail state as an observable acquisition boundary. No upstream issue filed yet.

## Changes

- Remove the `Page.files` fallback that created an empty `PageFileCollection` when `_files` stayed `None`.
- Raise `NotFoundException("Cannot find page files")` after automatic acquisition fails to populate `_files`.
- Preserve the successful "no files" case: a valid `files/PageFilesModule` response with no file rows still returns an empty collection.
- Add property-level tests for both successful empty responses and exhausted retry responses.
- Keep `PageCollection.get_page_files()` batching, retry behavior, parsing, and partial-success semantics unchanged.

## Type Of Change

- [x] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update
- [ ] Refactoring
- [ ] Security/privacy hardening
- [x] Reliability improvement
- [x] Test addition/modification
- [ ] CI/CD or build related

## Requirements Traceability

| Requirement | Acceptance | Verification | Negative Control |
| --- | --- | --- | --- |
| R1: Exhausted file-list retry is visible to property callers | `Page.files` raises `NotFoundException` when `get_page_files()` leaves `_files` unset | `test_files_property_raises_when_retry_is_exhausted` | The test failed before the fix with `DID NOT RAISE` because `_files` became `[]` |
| R2: Real empty file-list responses remain empty collections | A successful `files/PageFilesModule` response with no file rows returns a cached empty `PageFileCollection` | `test_files_property_auto_acquire_empty_response` | The exhausted-retry test proves failures no longer use the same empty result path |
| R3: Existing collection behavior is preserved | Batched file fetches still use `amc_request_with_retry`, skip exhausted pages, and preserve successful pages | `tests/unit/test_page.py` full module | Existing collection partial-success tests remain green |

## Testing

Local implementation commit: `771744a fix(page): surface failed file fetches`

- [x] `uv run --extra test pytest tests/unit/test_page.py::TestPageProperties::test_files_property_raises_when_retry_is_exhausted -q` failed before the fix with `DID NOT RAISE` and passed after the fix.
- [x] `uv run --extra test pytest tests/unit/test_page.py::TestPageProperties::test_files_property_auto_acquire_empty_response -q`
- [x] `uv run --extra test pytest tests/unit/test_page.py::TestPageProperties -q` passed with 9 tests.
- [x] `uv run --extra test pytest tests/unit/test_page.py -q` passed with 82 tests.
- [x] `uv run --extra test pytest tests/unit -q` passed with 580 tests.
- [x] `uv run ruff check .`
- [x] `uv run ruff format --check .`
- [x] `uv run mypy src tests`
- [x] `git diff --check`
- [x] `python3 /home/roku/.codex/skills/complexity-optimizer/scripts/analyze_complexity.py /home/roku/codex-thread-workspaces/019e8a3a-20fd-7113-975d-8c92336695cd/worktrees/wikidot.py --format markdown` refreshed the current complexity leads.

## Acceptance Criteria

- `Page.files` no longer converts an exhausted retry or missing file-list acquisition into a successful empty collection.
- `Page.files` raises `NotFoundException` when automatic file-list acquisition leaves `_files` unset.
- A valid response representing a page with no attached files still returns an empty `PageFileCollection`.
- Existing batched file fetch, partial-success, retry, and cached-detail behavior remains unchanged.
- No browser automation, live Wikidot mutation, upstream issue, or upstream PR is performed by this local slice.

## Upstream-Safe Motivation

Attached-file presence and absence are often meaningful data. A library should not make a failed file-list fetch indistinguishable from a successful empty file list, especially when collection-level code already preserves the missing state after retry exhaustion. This change makes `Page.files` consistent with `Page.source` and `Page.votes`, which raise when automatic acquisition does not populate the requested data.

## Local Evidence, Not For Upstream Paste

- Local rollout evidence included browser-free publishing, attachment inspection, source/corpus workflows, and page-evidence checks where file presence or absence can affect the result.
- Existing local issue [010-pr-retry-batched-file-fetches.md](010-pr-retry-batched-file-fetches.md) already established that exhausted file-list retries should leave failed pages unacquired rather than parsed as empty.
- The refreshed complexity scan still flags page detail acquisition paths as high-value surfaces; this fix keeps the change narrow instead of introducing a broader page-detail abstraction.
- This draft is local-only. Do not paste private rollout paths, local account names, thread workspace paths, raw command transcripts, or sandbox details into an upstream PR.

## Additional Notes

This slice does not change `PageFileCollection.acquire(...)`, file parsing, file URL normalization, batched request construction, retry policy, or partial-success handling. It only removes the property-level fallback that hid a failed acquisition behind an empty collection.
