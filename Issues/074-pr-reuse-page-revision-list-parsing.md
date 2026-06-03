# PR Draft: Reuse Page Revision List Parsing For Duplicate Page IDs

## Summary

`PageCollection.get_page_revisions()` already deduplicates duplicate uncached `Page` objects by resolved `page.id` before sending `history/PageRevisionListModule` requests, then populates each duplicate page object with its own `PageRevisionCollection`. The duplicate page objects still reparsed the same successful revision-list response body, reran revision creator parsing, and reran revision timestamp parsing for each page object in the duplicate ID group.

This fix parses each successful revision-list response once per unique page ID, stores the parsed revision fields, then creates page-owned `PageRevision` instances for every duplicate `Page` object in that page-ID group. The public `PageCollection` shape, duplicate page entries, page-owned revision collections, retry behavior, and malformed-row errors remain unchanged.

## Related Issue

Builds directly on [063-pr-deduplicate-page-revision-list-fetches.md](063-pr-deduplicate-page-revision-list-fetches.md), which removed duplicate revision-list requests while preserving duplicate page objects. It follows the duplicate-response parse reuse pattern from [073-pr-reuse-private-message-detail-parsing.md](073-pr-reuse-private-message-detail-parsing.md).

No upstream issue was filed from this local workspace.

## Changes

- Parse each unique successful `history/PageRevisionListModule` response once inside `PageCollection._acquire_page_revisions(...)`.
- Reuse parsed revision ID, revision number, creator, timestamp, and comment fields for duplicate page objects with the same resolved page ID.
- Preserve distinct `PageRevisionCollection` instances and distinct `PageRevision` objects for every duplicate page object.
- Preserve `PageRevision.page` ownership by constructing fresh revision objects for each owning page.
- Preserve first-seen request deduplication, cached-revision skipping, retry-aware AMC, `None` retry-result handling, malformed-row errors, lazy `Page.revisions`, and `Page.latest_revision` behavior.
- Strengthen the duplicate page-ID regression test to assert one response JSON parse and one user/date parse per revision row, not per duplicate page object.

## Type Of Change

- Performance improvement
- Refactoring
- Test addition/modification

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| Duplicate page IDs should not reparse the same revision-list response body. | `TestPageCollectionAcquire.test_acquire_revisions_deduplicates_duplicate_page_ids` asserts `response.json.call_count == 1` for two duplicate page objects sharing one successful response. | Regressions that move JSON parsing into the duplicate-page loop would fail this count. |
| Duplicate page IDs should not rerun revision creator/date parsing for duplicate page objects. | The focused test asserts `mock_user_parser.call_count == 3` and `mock_odate_parser.call_count == 3` for a three-row revision list shared by two duplicate page objects. | The RED test failed before the fix with `assert 6 == 3` for `mock_user_parser.call_count`. |
| Duplicate page objects still receive page-owned revision collections. | The focused test still asserts both pages have revision collections and that each collection's first `PageRevision.page` points at the owning page object. | Sharing one collection or one revision object across duplicate pages would fail the ownership assertions. |
| Existing page revision behavior stays green. | `uv run --extra test pytest tests/unit/test_page.py tests/unit/test_page_revision.py tests/unit/test_page_file.py -q`; `uv run --extra test pytest tests/unit -q`. | Regressions in revision parsing, lazy revision access, adjacent page-detail paths, or broad unit behavior reject the local completion claim. |
| Static quality gates remain green. | `uv run ruff check .`; `uv run ruff format --check .`; `uv run mypy src tests`; `git diff --check`. | Formatting, lint, type, or whitespace failures reject the local completion claim. |
| Complexity evidence is interpreted conservatively. | The refreshed scanner artifact still flags remaining `page.py` and `page_revision.py` loops; the claimed improvement is duplicate revision-list parse reuse, not removal of all page/revision complexity warnings. | Overclaiming that page/revision scanner warnings disappeared would reject the draft. |

## Testing

Implemented locally in commit `bf8e50f perf(page): reuse parsed duplicate revisions`.

- RED: `uv run --extra test pytest tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_revisions_deduplicates_duplicate_page_ids -q` failed before the fix with `assert 6 == 3` for `mock_user_parser.call_count`.
- GREEN: `uv run --extra test pytest tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_revisions_deduplicates_duplicate_page_ids -q`
- `uv run --extra test pytest tests/unit/test_page.py tests/unit/test_page_revision.py tests/unit/test_page_file.py -q` passed 149 tests.
- `uv run --extra test pytest tests/unit -q` passed 628 tests.
- `uv run ruff check .`
- `uv run ruff format --check .`
- `uv run mypy src tests`
- `git diff --check`
- `python3 /home/roku/.codex/skills/complexity-optimizer/scripts/analyze_complexity.py /home/roku/codex-thread-workspaces/019e8a3a-20fd-7113-975d-8c92336695cd/worktrees/wikidot.py --format markdown` refreshed current complexity leads.

Not run: `uv run pyright src tests` because this environment could not spawn the `pyright` executable.

## Acceptance Criteria

- Duplicate uncached `Page` objects with the same resolved `page.id` still send one revision-list request.
- A successful revision-list response is parsed once per unique page ID.
- Revision creator and timestamp parsers run once per revision row in the shared response, not once per duplicate page object.
- Each duplicate page object receives its own `PageRevisionCollection`.
- Each duplicate page object's `PageRevision` instances point back to that owning page object.
- First-seen unique page ID request order remains unchanged.
- Cached revision collections are still skipped.
- A `None` retry result still leaves the affected page ID group unacquired.
- Malformed revision rows still raise `NoElementException` with the affected revision ID and the first page in that page-ID group.
- Existing lazy `Page.revisions`, `Page.latest_revision`, page revision source/HTML acquisition, page ID acquisition, and mutation paths remain unchanged.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Revision history is a read-heavy evidence surface for page inspection, history comparison, source auditing, publication verification, and rollback workflows. Once duplicate page objects share the same resolved page ID and successful revision-list response, reparsing the same HTML and reparsing the same revision creator/date metadata does not add information. Reusing parsed fields reduces avoidable CPU work while preserving page-owned revision objects.

## Local Evidence, Not For Upstream Paste

- [063-pr-deduplicate-page-revision-list-fetches.md](063-pr-deduplicate-page-revision-list-fetches.md) removed duplicate revision-list requests but intentionally preserved duplicate page object outputs.
- The focused RED test demonstrated the remaining cost: duplicate page objects still parsed the same three-row revision list twice.
- The refreshed complexity scan continues to flag `src/wikidot/module/page.py` around revision-list parsing and adjacent page loops; this slice addresses duplicate parse fan-out only.
- Keep local rollout paths, account names, and corpus-specific identifiers out of any upstream discussion.

## Additional Notes

This slice does not change page source acquisition, page file acquisition, page vote acquisition, page revision source/HTML acquisition, revision row selectors, date parsing semantics, user parsing semantics, lazy property behavior, or mutation paths. It only avoids redoing the same successful revision-list parse for duplicate `Page` objects that share a resolved page ID.
