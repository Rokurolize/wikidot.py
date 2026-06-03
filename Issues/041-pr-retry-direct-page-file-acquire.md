# PR Draft: Retry Direct Page File Acquisition

## Summary

`PageFileCollection.acquire(page)` is a public direct file-list acquisition helper for a single page. Collection-level file acquisition already uses `site.amc_request_with_retry(...)`, and `Page.files` now surfaces failed automatic acquisition instead of fabricating an empty collection. The direct helper still used the plain `site.amc_request(...)` path, so transient AMC failures could be parsed as responses and fail with an attribute/parsing error before the library's retry behavior had a chance to run.

The fix routes `PageFileCollection.acquire(page)` through `site.amc_request_with_retry(...)`. If retries are exhausted and the retry helper returns `None`, the method now raises `UnexpectedException("Cannot retrieve page files")` instead of trying to parse a missing response.

## Related Issue

Complements [010-pr-retry-batched-file-fetches.md](010-pr-retry-batched-file-fetches.md), which made collection-level file fetches retry-aware, and [039-pr-page-files-exhausted-retry-error.md](039-pr-page-files-exhausted-retry-error.md), which made `Page.files` preserve failed acquisition visibility. No upstream issue filed yet.

## Changes

- Use `page.site.amc_request_with_retry(...)` in `PageFileCollection.acquire(page)`.
- Raise `UnexpectedException("Cannot retrieve page files")` when the direct file-list request exhausts retries.
- Add a public direct-acquire regression where plain AMC would have exposed a transient exception object but retry-aware AMC succeeds.
- Add an exhausted-retry regression for direct file acquisition.
- Update existing direct-acquire parsing tests to use the retry-aware request path.
- Keep file-row parsing, URL normalization, size parsing, empty-list handling, and invalid-row skipping unchanged.

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
| R1: Direct page-file acquisition uses retry-aware AMC | `PageFileCollection.acquire(page)` calls `page.site.amc_request_with_retry(...)` and does not call plain `amc_request(...)` | `test_acquire_uses_retry_aware_amc` | The test failed before the fix with `AttributeError: 'RuntimeError' object has no attribute 'json'` |
| R2: Exhausted direct file acquisition fails explicitly | `PageFileCollection.acquire(page)` raises `UnexpectedException("Cannot retrieve page files")` when retry returns `None` | `test_acquire_raises_when_retry_is_exhausted` | A missing response is not parsed and no empty collection is returned |
| R3: Existing successful parsing behavior is preserved | Successful file-list responses still parse file IDs, names, URLs, MIME types, sizes, empty responses, and invalid rows as before | `tests/unit/test_page_file.py` full module | Existing direct parsing tests remain green after moving to retry-aware AMC |

## Testing

Local implementation commit: `d75bb8a fix(page_file): retry direct file acquisition`

- [x] `uv run --extra test pytest tests/unit/test_page_file.py::TestPageFileCollectionAcquire::test_acquire_uses_retry_aware_amc -q` failed before the fix with `AttributeError: 'RuntimeError' object has no attribute 'json'` and passed after the fix.
- [x] `uv run --extra test pytest tests/unit/test_page_file.py::TestPageFileCollectionAcquire::test_acquire_raises_when_retry_is_exhausted -q`
- [x] `uv run --extra test pytest tests/unit/test_page_file.py::TestPageFileCollectionAcquire -q` passed with 8 tests.
- [x] `uv run --extra test pytest tests/unit/test_page_file.py -q` passed with 26 tests.
- [x] `uv run --extra test pytest tests/unit -q` passed with 583 tests.
- [x] `uv run ruff check .`
- [x] `uv run ruff format --check .`
- [x] `uv run mypy src tests`
- [x] `git diff --check`
- [x] `python3 /home/roku/.codex/skills/complexity-optimizer/scripts/analyze_complexity.py /home/roku/codex-thread-workspaces/019e8a3a-20fd-7113-975d-8c92336695cd/worktrees/wikidot.py --format markdown` refreshed the current complexity leads.

## Acceptance Criteria

- `PageFileCollection.acquire(page)` uses `page.site.amc_request_with_retry(...)`, not plain `page.site.amc_request(...)`.
- Exhausted retry for direct file acquisition raises `UnexpectedException`.
- Successful direct acquisition still returns a `PageFileCollection` with the parsed files.
- Empty file-list responses still return an empty `PageFileCollection`.
- Existing file parsing behavior for absolute URLs, malformed row IDs, invalid rows, and size units remains unchanged.
- No browser automation, live Wikidot mutation, upstream issue, or upstream PR is performed by this local slice.

## Upstream-Safe Motivation

Direct file acquisition and collection-level file acquisition should have the same reliability model. Without this change, callers that use the public `PageFileCollection.acquire(page)` helper can still hit transient AMC failures even though the surrounding page-file APIs are retry-aware. This is a small consistency fix that improves read reliability without changing the public return type or parser behavior for successful responses.

## Local Evidence, Not For Upstream Paste

- Local rollout evidence included browser-free publishing, attachment inspection, source/corpus workflows, and page-evidence checks where file presence or absence can affect downstream decisions.
- Existing local issue [010-pr-retry-batched-file-fetches.md](010-pr-retry-batched-file-fetches.md) established file-list acquisition as a retry-sensitive page-detail surface.
- Existing local issue [039-pr-page-files-exhausted-retry-error.md](039-pr-page-files-exhausted-retry-error.md) intentionally left `PageFileCollection.acquire(...)` unchanged; this draft covers that remaining public direct-acquire path.
- The refreshed complexity scan still flags `src/wikidot/module/page_file.py` as a page-detail acquisition hotspot, supporting this narrow direct-path reliability fix.
- This draft is local-only. Do not paste private rollout paths, local account names, thread workspace paths, raw command transcripts, or sandbox details into an upstream PR.

## Additional Notes

This slice does not change `Page.files`, `PageCollection.get_page_files()`, file parsing, URL normalization, size parsing, or collection inheritance behavior. It only moves the direct single-page file-list request to the same retry-aware AMC path already used by collection-level file acquisition.
