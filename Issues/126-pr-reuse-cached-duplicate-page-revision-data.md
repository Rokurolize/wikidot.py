# PR Draft: Reuse Cached Duplicate Page Revision Source And HTML

## Summary

`PageRevisionCollection.get_sources()` and `PageRevisionCollection.get_htmls()` already skip revisions whose source or HTML is cached, and they already deduplicate uncached duplicate revision IDs before fetching `history/PageSourceModule` or `history/PageVersionModule`. Before this fix, a collection containing both a cached revision and an uncached duplicate with the same revision ID still fetched source or HTML for the uncached duplicate instead of reusing the cached data already present in the same collection.

This fix lets the shared `_generic_acquire(...)` helper index already acquired same-ID revisions, copy source or HTML to matching uncached duplicates before building AMC requests, and only fetch revision IDs that remain unresolved. Public collection membership and ordering remain unchanged.

## Related Issue

Builds directly on [061-pr-deduplicate-page-revision-fetches.md](061-pr-deduplicate-page-revision-fetches.md), which established that duplicate page revision IDs should not trigger duplicate source or HTML requests. It also preserves the retry-aware source/HTML behavior from [015-pr-retry-revision-source-html-fetches.md](015-pr-retry-revision-source-html-fetches.md), the ViewSource text fidelity from [014-pr-preserve-viewsource-text.md](014-pr-preserve-viewsource-text.md), and the duplicate response parse reuse from [078-pr-reuse-page-revision-source-html-parsing.md](078-pr-reuse-page-revision-source-html-parsing.md).

No upstream issue was filed from this local workspace.

## Changes

- Add an optional same-ID cached-data copy hook to `PageRevisionCollection._generic_acquire(...)`.
- Reuse cached duplicate `PageSource` objects before constructing `history/PageSourceModule` requests.
- Reuse cached duplicate HTML strings before constructing `history/PageVersionModule` requests.
- Keep first-seen request order and existing uncached duplicate grouping for remaining unresolved revision IDs.
- Add focused regressions for cached source reuse and cached HTML reuse.
- Preserve retry-aware source/HTML fetches, failed retry handling, source text extraction, HTML separator parsing, lazy `PageRevision.source`, lazy `PageRevision.html`, revision-list acquisition, and adjacent page workflows.

## Type Of Change

- Performance/reliability improvement
- Cache behavior improvement
- Test addition/modification

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| Cached source from a duplicate revision ID must be reused within the same collection. | `TestPageRevisionCollection.test_get_sources_reuses_cached_duplicate_revision_source` asserts the uncached duplicate receives `cached revision source`. | The RED test failed before the fix because the duplicate source came from a new `history/PageSourceModule` fetch instead. |
| Cached HTML from a duplicate revision ID must be reused within the same collection. | `TestPageRevisionCollection.test_get_htmls_reuses_cached_duplicate_revision_html` asserts the uncached duplicate receives `<p>Cached revision HTML</p>`. | The RED test failed before the fix because the duplicate HTML came from a new `history/PageVersionModule` fetch instead. |
| Reusing cached duplicate source or HTML must avoid unnecessary network work. | The focused source and HTML tests assert neither plain `amc_request(...)` nor retry-aware `amc_request_with_retry(...)` is called. | A regression that fetches source or HTML for the duplicate fails the not-called assertions. |
| Existing revision source and HTML behavior remains intact. | `uv run pytest tests/unit/test_page_revision.py::TestPageRevisionCollection -q` passed 22 tests, and `uv run pytest tests/unit/test_page_revision.py -q` passed 32 tests. | Regressions in retry, exhausted retry, cached skipping, duplicate uncached propagation, source extraction, HTML separator parsing, or lazy behavior reject this local completion claim. |
| Adjacent page workflows stay green. | `uv run pytest tests/unit/test_page.py tests/unit/test_page_revision.py -q` passed 132 tests. | Regressions in page detail acquisition, revision-list acquisition, page source behavior, or lazy revision access reject this local completion claim. |
| Broad unit and static quality gates remain green. | `uv run pytest tests/unit -q`; `uv run ruff check .`; `uv run ruff format --check .`; `uv run mypy src tests`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject this local completion claim. |

## Testing

Implemented locally in commit `bc67044 perf(page_revision): reuse cached duplicate revision data`.

- RED: `uv run pytest tests/unit/test_page_revision.py::TestPageRevisionCollection::test_get_sources_reuses_cached_duplicate_revision_source -q` failed before the fix because the uncached duplicate was filled from a new source fetch instead of the already cached source.
- GREEN: `uv run pytest tests/unit/test_page_revision.py::TestPageRevisionCollection::test_get_sources_reuses_cached_duplicate_revision_source -q`
- RED: `uv run pytest tests/unit/test_page_revision.py::TestPageRevisionCollection::test_get_htmls_reuses_cached_duplicate_revision_html -q` failed before the fix because the uncached duplicate was filled from a new HTML fetch instead of the already cached HTML.
- GREEN: `uv run pytest tests/unit/test_page_revision.py::TestPageRevisionCollection::test_get_sources_reuses_cached_duplicate_revision_source tests/unit/test_page_revision.py::TestPageRevisionCollection::test_get_htmls_reuses_cached_duplicate_revision_html -q`
- `uv run pytest tests/unit/test_page_revision.py::TestPageRevisionCollection -q` passed 22 tests.
- `uv run pytest tests/unit/test_page_revision.py -q` passed 32 tests.
- `uv run pytest tests/unit/test_page.py tests/unit/test_page_revision.py -q` passed 132 tests.
- `uv run pytest tests/unit -q` passed 681 tests.
- `uv run ruff check .`
- `uv run ruff format --check .`
- `uv run mypy src tests`
- `git diff --check`

Not run: `uv run pyright src tests` because this environment could not find a `pyright` executable on PATH.

## Acceptance Criteria

- A cached source on one revision object is reused for uncached collection entries with the same revision ID.
- A cached HTML string on one revision object is reused for uncached collection entries with the same revision ID.
- No AMC source or HTML request is sent when every uncached revision can be satisfied from cached duplicates in the same collection.
- Uncached duplicate revision IDs with no cached source or HTML still use the existing one-request-per-ID fetch path.
- Exhausted retry results still leave only unresolved revision IDs unacquired.
- Existing source extraction, HTML separator handling, cached-data skipping, duplicate uncached grouping, lazy `PageRevision.source`, lazy `PageRevision.html`, revision-list acquisition, and page parser behavior remain unchanged.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Page revision source and HTML collection is a read-heavy inspection workflow for history comparison, source auditing, publication verification, and rollback tooling. If a caller holds multiple `PageRevision` objects for the same revision ID and one already has source or HTML cached, fetching the same module again adds avoidable AMC work and another failure point. Reusing cached duplicate data keeps source/HTML acquisition consistent with the existing duplicate-ID dedupe rule while preserving the public collection shape.

## Local Evidence, Not For Upstream Paste

- Existing local drafts established page revision source and HTML reads as a practical rollout-backed surface for inspection, archiving, and audit workflows.
- Issue 061 already established duplicate page revision IDs as a realistic performance lead for source and HTML fetching.
- Issue 078 showed that after request deduplication, the same source/HTML response should be parsed once for duplicate uncached revision IDs; this slice applies the same "do no duplicate work" rule to already cached same-ID revisions.
- The refreshed complexity scan continues to flag `src/wikidot/module/page_revision.py` around source/HTML acquisition as a worthwhile audit area.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, and saved page contents out of upstream discussion.

## Additional Notes

This slice does not change revision source or HTML request construction, retry policy, source text normalization, HTML separator parsing rules, duplicate uncached grouping, lazy property return types, revision-list acquisition, page source fetching, publishing, or mutation methods. It only lets already cached source or HTML satisfy duplicate uncached revision entries in the same collection before any source/HTML fetch request is built.
