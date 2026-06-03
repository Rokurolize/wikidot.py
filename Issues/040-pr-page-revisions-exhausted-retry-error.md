# PR Draft: Surface Failed Page Revision Fetches

## Summary

`Page.revisions` automatically calls `PageCollection(...).get_page_revisions()` when revision history has not been loaded. The collection-level retry path intentionally leaves `page._revisions` as `None` when a page's `history/PageRevisionListModule` request exhausts retries, so callers can distinguish a failed fetch from a successfully parsed revision list.

The property layer erased that distinction by returning `PageRevisionCollection(self, None)` whenever `_revisions` stayed unset. A transient or exhausted revision-list failure could therefore look like a page with an empty revision history.

The fix raises `NotFoundException("Cannot find page revisions")` when automatic acquisition leaves `_revisions` unset. Successful revision-list responses still return the cached `PageRevisionCollection`.

## Related Issue

Complements [009-pr-skip-cached-page-detail-fetches.md](009-pr-skip-cached-page-detail-fetches.md), which treats revision, vote, and file detail caches as observable acquisition state. Also aligns with [039-pr-page-files-exhausted-retry-error.md](039-pr-page-files-exhausted-retry-error.md), which fixed the same property-layer failure masking for attached files. No upstream issue filed yet.

## Changes

- Make `Page.revisions` raise `NotFoundException("Cannot find page revisions")` after automatic acquisition fails to populate `_revisions`.
- Return the cached `PageRevisionCollection` directly when revision acquisition succeeds.
- Update the normal `Page.revisions` property test to assert the retry-aware AMC path is used.
- Add a property-level exhausted-retry regression test.
- Keep `PageCollection.get_page_revisions()` batching, retry behavior, parsing, and cache-aware partial-success semantics unchanged.

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
| R1: Exhausted revision-list retry is visible to property callers | `Page.revisions` raises `NotFoundException` when `get_page_revisions()` leaves `_revisions` unset | `test_revisions_property_raises_when_retry_is_exhausted` | The test failed before the fix with `DID NOT RAISE` because an empty `PageRevisionCollection` was returned |
| R2: Successful revision-list responses still return revisions | A successful `history/PageRevisionListModule` response returns the cached revision collection | `test_revisions_property` | The test asserts the retry-aware path is used and still parses 3 revisions |
| R3: Existing collection behavior is preserved | Batched revision fetches still use `amc_request_with_retry`, skip exhausted pages, and preserve successful pages | `tests/unit/test_page.py` full module | Existing collection acquisition and latest-revision tests remain green |

## Testing

Local implementation commit: `e95bebf fix(page): surface failed revision fetches`

- [x] `uv run --extra test pytest tests/unit/test_page.py::TestPageProperties::test_revisions_property_raises_when_retry_is_exhausted -q` failed before the fix with `DID NOT RAISE` and passed after the fix.
- [x] `uv run --extra test pytest tests/unit/test_page.py::TestPageProperties::test_revisions_property -q`
- [x] `uv run --extra test pytest tests/unit/test_page.py::TestPageProperties -q` passed with 10 tests.
- [x] `uv run --extra test pytest tests/unit/test_page.py -q` passed with 83 tests.
- [x] `uv run --extra test pytest tests/unit -q` passed with 581 tests.
- [x] `uv run ruff check .`
- [x] `uv run ruff format --check .`
- [x] `uv run mypy src tests`
- [x] `git diff --check`
- [x] `python3 /home/roku/.codex/skills/complexity-optimizer/scripts/analyze_complexity.py /home/roku/codex-thread-workspaces/019e8a3a-20fd-7113-975d-8c92336695cd/worktrees/wikidot.py --format markdown` refreshed the current complexity leads.

## Acceptance Criteria

- `Page.revisions` no longer converts an exhausted retry or missing revision-list acquisition into a successful empty revision collection.
- `Page.revisions` raises `NotFoundException` when automatic revision-list acquisition leaves `_revisions` unset.
- Successful revision-list acquisition still returns parsed revisions through the public property.
- Existing batched revision fetch, partial-success, retry, cached-detail, and latest-revision behavior remains unchanged.
- No browser automation, live Wikidot mutation, upstream issue, or upstream PR is performed by this local slice.

## Upstream-Safe Motivation

Revision history is a core evidence surface for page inspection, publishing checks, and rollback/source workflows. A failed revision-list fetch should not be indistinguishable from a successful empty history. This change makes `Page.revisions` consistent with `Page.source`, `Page.votes`, and `Page.files`, which now surface failed automatic acquisition instead of silently returning absent data.

## Local Evidence, Not For Upstream Paste

- Local rollout evidence included source collection, browser-free publishing, page-evidence checks, and page-detail workflows where revision presence and latest revision lookup can affect downstream decisions.
- Existing local issue [009-pr-skip-cached-page-detail-fetches.md](009-pr-skip-cached-page-detail-fetches.md) already treats `_revisions is None` as an acquisition boundary for retry/cache behavior.
- The refreshed complexity scan still flags page detail acquisition paths as high-value surfaces; this fix keeps the change narrow and behavior-preserving rather than introducing a broader page-detail abstraction.
- This draft is local-only. Do not paste private rollout paths, local account names, thread workspace paths, raw command transcripts, or sandbox details into an upstream PR.

## Additional Notes

This slice does not change `PageCollection.get_page_revisions()`, revision parsing, revision source/HTML retrieval, request construction, retry policy, or partial-success handling. It only removes the property-level empty-collection result that hid a failed revision-list acquisition.

Follow-up: [063-pr-deduplicate-page-revision-list-fetches.md](063-pr-deduplicate-page-revision-list-fetches.md) removes duplicate revision-list requests for repeated resolved page IDs while preserving this slice's failed-acquisition behavior.
