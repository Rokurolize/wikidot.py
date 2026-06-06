# PR Draft: Reject Boolean Source Iterator Batch Sizes

## Summary

`Site.pages.iter_sources(...)` validates `source_batch_size` and `fallback_batch_size` through the shared positive-integer helper added in Issue345, but that helper still used plain `isinstance(value, int)`. Because Python treats `bool` as an `int` subclass, `source_batch_size=True` was accepted as a one-page primary source batch, `fallback_batch_size=True` was accepted as a one-page fallback batch, and `False` values were classified as range failures rather than type failures.

This change treats boolean source iterator batch-size controls as malformed integers at the public `iter_sources(...)` boundary. Valid positive integers, existing string/float validation, existing non-positive range validation, search order, source batching, fallback retries, required-tag filtering, source result fields, and adjacent ListPages behavior remain unchanged.

## Outcome

Source collection callers now get deterministic validation for boolean batch-size controls instead of accidentally accepting booleans as integer chunk sizes or reporting `False` as a range error.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use `Site.pages.iter_sources(...)` for bounded page-source collection, fallback source retries, or audit-friendly source result ledgers.

## Current Evidence

Local rollout evidence repeatedly uses broad ListPages and source iterator workflows with explicit `limit`, `perPage`, `source_batch_size`, and `fallback_batch_size` values to keep corpus/source collection bounded. Existing drafts [004-feature-large-corpus-page-source-collection.md](004-feature-large-corpus-page-source-collection.md), [019-pr-page-source-iterator-fallback.md](019-pr-page-source-iterator-fallback.md), [022-pr-source-iterator-large-fallback-batch.md](022-pr-source-iterator-large-fallback-batch.md), [049-pr-filter-iterators-by-required-tags.md](049-pr-filter-iterators-by-required-tags.md), [051-pr-preserve-source-batch-successes.md](051-pr-preserve-source-batch-successes.md), [068-pr-preserve-required-tag-search-chunk-size.md](068-pr-preserve-required-tag-search-chunk-size.md), [052-pr-source-result-context-properties.md](052-pr-source-result-context-properties.md), [331-pr-page-source-response-body-type-context.md](331-pr-page-source-response-body-type-context.md), [344-pr-validate-search-pagination-types.md](344-pr-validate-search-pagination-types.md), [345-pr-validate-source-iterator-batch-sizes.md](345-pr-validate-source-iterator-batch-sizes.md), [409-pr-reject-boolean-search-pagination-values.md](409-pr-reject-boolean-search-pagination-values.md), and [408-pr-reject-boolean-publish-visibility-controls.md](408-pr-reject-boolean-publish-visibility-controls.md) establish this as a practical iterator and diagnostics surface.

Those prior slices are not duplicates. Issue345 rejected string and float source iterator batch sizes, while preserving positive integer controls and existing range errors. It did not reject booleans, which still passed the integer type check because of Python's bool/int relationship. Issue409 and Issue408 fixed the same bool-as-int pattern on adjacent search pagination and publish visibility controls, not the source iterator batch-size controls.

## Related Issue

Builds directly on [345-pr-validate-source-iterator-batch-sizes.md](345-pr-validate-source-iterator-batch-sizes.md). This slice preserves that issue's string/float diagnostics and adds the missing boolean exclusion for the same positive-integer helper.

No upstream issue was filed from this local workspace.

## Changes

- Reject `Site.pages.iter_sources(source_batch_size=True or False)` with `ValueError("source_batch_size must be an integer")`.
- Reject `Site.pages.iter_sources(fallback_batch_size=True or False)` with `ValueError("fallback_batch_size must be an integer")`.
- Preserve existing valid positive integer source and fallback batch-size behavior.
- Preserve existing string/float and non-positive batch-size validation messages.
- Preserve existing source iterator search order, source chunking, fallback retry, per-page failure records, source result fields, and required-tag filtering.

## Type Of Change

- Input validation
- Public API behavior hardening
- Source iterator preflight safety
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `Site.pages.iter_sources(source_batch_size=True or False)` must reject the value with `ValueError("source_batch_size must be an integer")` before ListPages search, primary source fetches, or chunk comparison logic begins. |
| R2 | `Site.pages.iter_sources(fallback_batch_size=True or False)` must reject the value with `ValueError("fallback_batch_size must be an integer")` before ListPages search, primary source fetches, fallback source fetches, or fallback `range(...)` traversal begins. |
| R3 | Existing non-boolean batch-size validation must remain unchanged for valid positive integers, malformed strings/floats, and non-positive integer values. |
| R4 | Existing `iter_sources(...)`, `iter_search(...)`, required-tag filtering, source fallback, source result context fields, and ListPages behavior must remain unchanged. |
| R5 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R6 | Focused RED/GREEN, source iterator tests, adjacent page/search/source tests, full unit tests, lint, format, type, and whitespace gates must pass before claiming this local implementation complete; unavailable tools must be reported instead of hidden. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Boolean source batch sizes fail with the same integer-type diagnostic used for malformed non-integer source batch sizes. | New `TestSitePagesAccessor.test_iter_sources_batch_sizes_reject_booleans_before_search` failed RED because `source_batch_size=True` did not raise and `source_batch_size=False` reported a range error, then passed GREEN after `bool` exclusion was added. | Treating `True` as batch size `1`, classifying `False` as a range error, calling `PageCollection.search_pages(...)`, or reaching source fetch logic rejects this local completion claim. | Source iterator public API boundary | `src/wikidot/module/site.py`, `tests/unit/test_site.py` |
| R2 | Boolean fallback batch sizes fail with the same integer-type diagnostic used for malformed non-integer fallback batch sizes. | The same focused regression failed RED because `fallback_batch_size=True` did not raise and `fallback_batch_size=False` reported a range error, then passed GREEN after `bool` exclusion was added. | Treating `True` as fallback chunk size `1`, classifying `False` as a range error, calling `PageCollection.search_pages(...)`, reaching fallback `range(...)`, or source-fetching pages rejects this local completion claim. | Source iterator fallback preflight | `src/wikidot/module/site.py`, `tests/unit/test_site.py` |
| R3 | Existing query construction, string/float type checks, positive integer chunking, and range contracts remain compatible. | `tests/unit/test_site.py::TestSitePagesAccessor` passed 20 tests after the boolean rejection was added. | Changing valid chunk sizes, changing string/float diagnostics, changing `<= 0` diagnostics, result order, primary source batch sizes, fallback retry chunks, missing-page retry behavior, or per-page failure records rejects this local completion claim. | Source iterator behavior | `tests/unit/test_site.py` |
| R4 | Existing page search and iterator behavior remains green. | Adjacent page/search/source tests passed 256 tests; full unit tests passed 1454 tests. | Regressing `iter_search(...)`, `iter_sources(...)`, required-tag filtering, source fallback, source result fields, search pagination validation, tag-list validation, parent-fullname validation, ListPages parsing, or page collection behavior rejects this local completion claim. | Page/source collection workflows | `tests/unit/test_site.py`, `tests/unit/test_page.py`, `tests/unit/test_search_pages_query.py`, `tests/unit` |
| R5 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level tests only. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, or live Wikidot actions rejects this local completion claim. | Test and draft privacy | this draft |
| R6 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, source iterator class tests passed, adjacent page/search/source tests passed, full unit passed, ruff, format, mypy, and whitespace checks passed; pyright was unavailable. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `2797f77 fix(site): reject boolean source iterator batch sizes`.

- RED: `uv run --extra test pytest tests/unit/test_site.py::TestSitePagesAccessor::test_iter_sources_batch_sizes_reject_booleans_before_search -q` failed before the fix with 4 failures: `True` values did not raise, and `False` values raised `... must be greater than 0` instead of the integer-type diagnostic.
- GREEN: `uv run --extra test pytest tests/unit/test_site.py::TestSitePagesAccessor::test_iter_sources_batch_sizes_reject_booleans_before_search -q` passed 4 tests.
- `uv run --extra test pytest tests/unit/test_site.py::TestSitePagesAccessor -q` passed 20 tests.
- `uv run --extra test pytest tests/unit/test_site.py::TestSitePagesAccessor tests/unit/test_page.py tests/unit/test_search_pages_query.py -q` passed 256 tests.
- `uv run ruff format src/wikidot/module/site.py tests/unit/test_site.py` reformatted 1 file and left 1 file unchanged.
- `uv run --extra test pytest tests/unit -q` passed 1454 tests.
- `uv run ruff check` passed.
- `uv run ruff format --check` passed with 81 files already formatted.
- `uv run mypy src tests` passed with no issues in 81 source files.
- `git diff --check` passed.

Not run successfully: `uv run pyright src tests` failed because this environment could not spawn a `pyright` executable.

## Acceptance Criteria

- `Site.pages.iter_sources(source_batch_size=True)` and `Site.pages.iter_sources(source_batch_size=False)` raise `ValueError("source_batch_size must be an integer")` before `PageCollection.search_pages(...)`.
- `Site.pages.iter_sources(fallback_batch_size=True)` and `Site.pages.iter_sources(fallback_batch_size=False)` raise `ValueError("fallback_batch_size must be an integer")` before `PageCollection.search_pages(...)`.
- Existing `source_batch_size="2"`, `source_batch_size=1.5`, `fallback_batch_size="1"`, and `fallback_batch_size=1.5` validation remains unchanged.
- Existing `source_batch_size <= 0` and `fallback_batch_size <= 0` validation remains unchanged for non-boolean integers.
- Existing valid source iterator chunking, fallback retry behavior, required-tag filtering, source result fields, ListPages search, and adjacent page/search tests remain green.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

Source iterator batch sizes are numeric control-plane values for chunked source retrieval and fallback retries. Boolean values from JSON, YAML, generated structures, or flag parsing should fail at the iterator boundary instead of silently becoming one-page batches or producing misleading range diagnostics.

## Local Evidence, Not For Upstream Paste

- Local rollout evidence used bounded ListPages and source iterator workflows with explicit source/fallback batch sizes and per-page source failure records.
- Existing local drafts covered source iterator creation, fallback retry behavior, large fallback chunks, result ledger fields, required-tag filtering, response-body diagnostics, string/float batch-size type validation, and search pagination boolean rejection, but did not cover boolean `iter_sources(...)` batch-size controls.
- The focused RED failures showed `True` accepted as a batch size and `False` classified as a range failure. The GREEN regression covers `True` and `False` for both source and fallback batch-size fields.
- This slice only rejects boolean source iterator batch-size values; it does not change valid source batching, fallback retry order, missing-page retry policy, per-page error reporting, result ledger fields, ListPages search, required-tag filtering, live site behavior, or parsing.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw login response bodies, and private site data out of upstream discussion.

## Additional Notes

The change intentionally rejects malformed batch-size types instead of coercing them. Callers that load source iterator batch sizes from JSON, YAML, CLI flags, spreadsheets, generated structures, or environment variables should resolve those values into real integers before calling `Site.pages.iter_sources(...)`.
