# PR Draft: Deduplicate Page Revision Source And HTML Fetch IDs

## Summary

`PageRevisionCollection.get_sources()` and `PageRevisionCollection.get_htmls()` share `_generic_acquire(...)` to batch `history/PageSourceModule` and `history/PageVersionModule` requests. Duplicate `PageRevision.id` entries previously sent duplicate source or HTML requests while public collection entries stayed duplicated.

This fix deduplicates uncached revision IDs inside `_generic_acquire(...)`, preserves first-seen request order, applies one successful response to every duplicate entry, and preserves cached-source/HTML skipping, retry-aware AMC, `None` retry-result handling, parsing, and lazy `PageRevision.source` / `PageRevision.html` acquisition.

## Related Issue

Builds on [015-pr-retry-revision-source-html-fetches.md](015-pr-retry-revision-source-html-fetches.md) by preserving its retry-aware revision source/HTML behavior while removing duplicate requests for repeated page revision IDs. It follows the same local request-deduplication pattern as [055-pr-deduplicate-forum-post-source-fetches.md](055-pr-deduplicate-forum-post-source-fetches.md), [057-pr-deduplicate-forum-post-revision-html-fetches.md](057-pr-deduplicate-forum-post-revision-html-fetches.md), and [058-pr-deduplicate-forum-post-revision-with-html-fetches.md](058-pr-deduplicate-forum-post-revision-with-html-fetches.md).

No upstream issue was filed from this local workspace.

## Changes

- Group uncached `PageRevision` entries by `revision.id` in `_generic_acquire(...)`.
- Send one `history/PageSourceModule` or `history/PageVersionModule` request per first-seen uncached revision ID.
- Apply each successful source or HTML response to every unacquired duplicate entry with the same revision ID.
- Preserve cached item skipping, retry behavior, `None` response handling, source text parsing, HTML separator parsing, and lazy `PageRevision.source` / `PageRevision.html` behavior.
- Add focused tests for duplicate IDs in both `get_sources()` and `get_htmls()`.

## Type Of Change

- Performance and reliability improvement
- Test-covered behavior fix

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| Avoid duplicate page revision source fetches for repeated uncached revision IDs. | `TestPageRevisionCollection.test_get_sources_deduplicates_duplicate_revision_ids` asserts one `history/PageSourceModule` request and both entries receiving source. | Reverting the deduplication either sends duplicate source requests or leaves a duplicate entry unacquired. |
| Avoid duplicate page revision HTML fetches for repeated uncached revision IDs. | `TestPageRevisionCollection.test_get_htmls_deduplicates_duplicate_revision_ids` asserts one `history/PageVersionModule` request and both entries receiving HTML. | The RED test failed with `ValueError: zip() argument 2 is shorter than argument 1` when duplicate entries outnumbered responses. |
| Keep duplicate collection entries semantically visible to callers. | Both duplicate entries remain in the collection and receive the same successful source or HTML content. | Collapsing the public collection would change iteration length and ordering. |
| Preserve existing revision source/HTML behavior. | `uv run --extra test pytest tests/unit/test_page_revision.py -q`; `uv run --extra test pytest tests/unit/test_page.py tests/unit/test_page_revision.py tests/unit/test_site.py -q`; `uv run --extra test pytest tests/unit -q`; lint, format, type, and whitespace checks. | Regression would break existing parsing, retry, lazy acquisition, or adjacent page/site tests. |

## Testing

Implemented locally in commit `53a8b45 perf(page_revision): deduplicate revision batch fetch ids`.

- RED: `uv run --extra test pytest tests/unit/test_page_revision.py::TestPageRevisionCollection::test_get_htmls_deduplicates_duplicate_revision_ids -q` failed before the fix with `ValueError: zip() argument 2 is shorter than argument 1`.
- GREEN: `uv run --extra test pytest tests/unit/test_page_revision.py::TestPageRevisionCollection::test_get_htmls_deduplicates_duplicate_revision_ids -q`
- `uv run --extra test pytest tests/unit/test_page_revision.py -q` passed 30 tests.
- `uv run --extra test pytest tests/unit/test_page.py tests/unit/test_page_revision.py tests/unit/test_site.py -q` passed 168 tests.
- `uv run --extra test pytest tests/unit -q` passed 616 tests.
- `uv run ruff check src/wikidot/module/page_revision.py tests/unit/test_page_revision.py`
- `uv run ruff check .`
- `uv run ruff format --check .`
- `uv run mypy src tests`
- `git diff --check`

## Acceptance Criteria

- Duplicate uncached revision IDs are fetched once for sources.
- Duplicate uncached revision IDs are fetched once for HTML.
- Request order remains the first-seen order from the collection.
- The public collection length, ordering, and duplicate entries remain unchanged.
- Every unacquired duplicate entry receives the same successful source or HTML content.
- A `None` retry result leaves that revision ID group unacquired, preserving lazy retry semantics.
- Cached entries are still skipped.
- Lazy `PageRevision.source`, lazy `PageRevision.html`, source extraction, HTML separator handling, revision list acquisition, retry policy, and mutation methods are unchanged.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Page revision inspection is read-heavy in history comparison, source auditing, publication verification, and resumable corpus ledgers. If a caller accidentally carries duplicate `PageRevision` objects for the same revision ID, the collection should not issue duplicate source or HTML requests just to populate duplicate entries.

## Local Evidence, Not For Upstream Paste

- Local revision and source collection hardening has accumulated through [014-pr-surface-failed-revision-fetches.md](014-pr-surface-failed-revision-fetches.md), [015-pr-retry-revision-source-html-fetches.md](015-pr-retry-revision-source-html-fetches.md), [026-pr-report-publish-create-outcome.md](026-pr-report-publish-create-outcome.md), and [051-pr-preserve-source-batch-successes.md](051-pr-preserve-source-batch-successes.md).
- The same duplicate-ID request pattern was previously found and fixed for private message details, forum post sources, forum post revisions, forum post revision HTML, and forum thread post/detail acquisition in local drafts 054 through 060.
- Keep local rollout paths, account names, and corpus-specific identifiers out of any upstream discussion.

## Additional Notes

This does not change revision-list acquisition, ordering, parsing, lazy return types, current page source fetching, publishing, or mutation methods. It only removes duplicate source and HTML requests for repeated uncached page revision IDs.

Follow-up: [063-pr-deduplicate-page-revision-list-fetches.md](063-pr-deduplicate-page-revision-list-fetches.md) removes duplicate page revision-list requests before individual revision source/HTML acquisition begins.
