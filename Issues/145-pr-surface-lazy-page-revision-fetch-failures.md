# PR Draft: Surface Lazy Page Revision Fetch Failures

## Summary

`PageRevisionCollection.get_sources()` and `get_htmls()` intentionally preserve partial batch successes: when `amc_request_with_retry(...)` returns `None` for one revision after exhausting retries, successful sibling revisions still receive their data and the failed revision remains uncached. Before this fix, the single-revision lazy properties `PageRevision.source` and `PageRevision.html` reused that batch helper but returned the still-uncached `None` value directly. That made a transient or exhausted retry failure look like a valid nullable property result even though the public property is the single-item read path.

This fix keeps batch behavior unchanged and adds an acquisition-aftercheck only to the lazy properties. If the single revision is still uncached after the retry-aware acquisition attempt, `source` raises `UnexpectedException("Cannot retrieve page revision source: ...")` and `html` raises `UnexpectedException("Cannot retrieve page revision HTML: ...")`.

## Related Issue

Builds on [015-pr-retry-revision-source-html-fetches.md](015-pr-retry-revision-source-html-fetches.md), which made revision source/HTML batch acquisition retry-aware, and [126-pr-reuse-cached-duplicate-page-revision-data.md](126-pr-reuse-cached-duplicate-page-revision-data.md), which reused cached same-ID revision source/HTML data.

No upstream issue was filed from this local workspace.

## Changes

- Import `UnexpectedException` in `page_revision.py`.
- Make `PageRevision.source` return `PageSource` and raise if the retry-aware lazy acquisition leaves `_source` unset.
- Make `PageRevision.html` return `str` and raise if the retry-aware lazy acquisition leaves `_html` unset.
- Add focused regressions for exhausted retry results from `revision.source` and `revision.html`.
- Keep `PageRevisionCollection.get_sources()` and `get_htmls()` partial-success semantics unchanged for batch callers.

## Type Of Change

- Bug fix
- Failure visibility improvement
- Test addition/modification

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| Lazy `PageRevision.source` must not return `None` after retry exhaustion. | `TestPageRevision.test_source_property_raises_when_retry_is_exhausted` asserts an `UnexpectedException` and verifies `history/PageSourceModule` uses `amc_request_with_retry(...)`. | The RED test failed before the fix because `source` returned `None` and did not raise. |
| Lazy `PageRevision.html` must not return `None` after retry exhaustion. | `TestPageRevision.test_html_property_raises_when_retry_is_exhausted` asserts an `UnexpectedException` and verifies `history/PageVersionModule` uses `amc_request_with_retry(...)`. | The RED test failed before the fix because `html` returned `None` and did not raise. |
| Batch source/HTML acquisition keeps partial-success behavior. | `uv run pytest tests/unit/test_page_revision.py -q` passed 34 tests, including the existing partial retry-response tests. | A change that raises from `get_sources()` or `get_htmls()` on a single `None` batch response rejects this local completion claim. |
| Page revision behavior remains stable for adjacent page workflows. | `uv run pytest tests/unit/test_page_revision.py tests/unit/test_page.py -q` passed 139 tests. | Regressions in page revision-list parsing, lazy page revisions, page source, page files, or page votes reject this local completion claim. |
| Broad unit and static quality gates remain green. | `uv run pytest tests/unit -q`; `uv run ruff check`; `uv run ruff format --check`; `uv run mypy src tests --install-types --non-interactive`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject this local completion claim. |

## Testing

Implemented locally in commit `33d0e15 fix(page_revision): surface lazy revision fetch failures`.

- RED: `uv run pytest tests/unit/test_page_revision.py::TestPageRevision::test_source_property_raises_when_retry_is_exhausted tests/unit/test_page_revision.py::TestPageRevision::test_html_property_raises_when_retry_is_exhausted -q` failed before the fix because both properties returned `None` and did not raise `UnexpectedException`.
- GREEN: `uv run pytest tests/unit/test_page_revision.py::TestPageRevision::test_source_property_raises_when_retry_is_exhausted tests/unit/test_page_revision.py::TestPageRevision::test_html_property_raises_when_retry_is_exhausted -q`
- `uv run pytest tests/unit/test_page_revision.py -q` passed 34 tests.
- `uv run pytest tests/unit/test_page_revision.py tests/unit/test_page.py -q` passed 139 tests.
- `uv run pytest tests/unit -q` passed 710 tests.
- `uv run ruff check`
- `uv run ruff format --check`
- `uv run mypy src tests --install-types --non-interactive`
- `git diff --check`

Not run: `uv run pyright` because this environment could not find a `pyright` executable.

## Acceptance Criteria

- `PageRevision.source` performs its existing lazy retry-aware acquisition when `_source` is unset.
- `PageRevision.source` raises `UnexpectedException` if `_source` remains unset after that acquisition attempt.
- `PageRevision.html` performs its existing lazy retry-aware acquisition when `_html` is unset.
- `PageRevision.html` raises `UnexpectedException` if `_html` remains unset after that acquisition attempt.
- Cached `source` and `html` values are returned unchanged without new AMC requests.
- `PageRevisionCollection.get_sources()` and `get_htmls()` still preserve partial batch successes and leave failed retry entries uncached.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Revision source and rendered HTML are often read through the ergonomic single-item properties after selecting a revision from page history. In that context, returning `None` after the retry-aware request path is misleading: callers asked for the single revision's source or HTML, and the library should surface that the remote read failed instead of handing back a value outside the property's useful contract. Batch helpers still retain the existing partial-success behavior for callers that explicitly process many revisions at once.

## Local Evidence, Not For Upstream Paste

- Local rollout-backed page-revision drafts repeatedly identified revision source/HTML reads as practical read-heavy surfaces: retry-aware fetching, duplicate-ID batching, cached duplicate reuse, response parse reuse, and page-history row parsing.
- This slice came from comparing the hardened batch retry behavior with the still-nullable lazy property path and then proving the silent failure with focused RED property tests.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, and saved page contents out of upstream discussion.

## Additional Notes

This slice does not change `PageRevisionCollection._generic_acquire(...)`, deduplication, response parsing, cache-copy behavior, retry policy, or batch partial-success behavior. It only makes the single-revision lazy properties fail visibly when their own acquisition attempt did not populate the requested value.
