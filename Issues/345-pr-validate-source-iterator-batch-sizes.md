# PR Draft: Validate Source Iterator Batch Size Types

## Summary

`Site.pages.iter_sources(...)` already rejected non-positive `source_batch_size` and `fallback_batch_size` values. A remaining boundary gap was type validation: `source_batch_size="2"` and `fallback_batch_size="1"` leaked raw Python comparison `TypeError` from the existing `<= 0` checks, while float values such as `source_batch_size=1.5` could pass the positive check and enter source iterator chunking logic.

This change validates both batch-size controls as integers before ListPages search, primary source fetches, fallback source retries, or fallback `range(...)` traversal begins. Invalid values now raise stable `ValueError` messages at the public API boundary.

## Outcome

Source collection callers now get deterministic validation for malformed source iterator batch-size controls instead of raw comparison errors, accidental float chunking, or deferred fallback traversal failures.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use `Site.pages.iter_sources(...)` for bounded page-source collection, fallback retries, or audit-friendly source result ledgers.

## Current Evidence

Local rollout evidence repeatedly uses broad ListPages and source-iterator workflows to collect page sources with explicit limits, page sizes, source batches, fallback retries, and per-page failure records. Existing drafts [004-feature-large-corpus-page-source-collection.md](004-feature-large-corpus-page-source-collection.md), [019-pr-page-source-iterator-fallback.md](019-pr-page-source-iterator-fallback.md), [022-pr-source-iterator-large-fallback-batch.md](022-pr-source-iterator-large-fallback-batch.md), [049-pr-filter-iterators-by-required-tags.md](049-pr-filter-iterators-by-required-tags.md), [051-pr-source-result-ledger-fields.md](051-pr-source-result-ledger-fields.md), [068-pr-preserve-required-tag-search-chunk-size.md](068-pr-preserve-required-tag-search-chunk-size.md), [069-pr-source-result-context-fields.md](069-pr-source-result-context-fields.md), [195-pr-forum-thread-list-user-parse-context.md](195-pr-forum-thread-list-user-parse-context.md), [225-pr-private-message-body-type-context.md](225-pr-private-message-body-type-context.md), [338-pr-source-response-body-type-context.md](338-pr-source-response-body-type-context.md), and [344-pr-validate-search-pagination-types.md](344-pr-validate-search-pagination-types.md) establish this as a practical iterator and diagnostics surface. Those slices covered source iteration, fallback retry behavior, result ledger fields, required-tag filtering, response-body diagnostics, and search pagination type validation; they did not cover non-integer `iter_sources(...)` batch-size controls.

## Related Issue

Builds directly on [019-pr-page-source-iterator-fallback.md](019-pr-page-source-iterator-fallback.md) and [022-pr-source-iterator-large-fallback-batch.md](022-pr-source-iterator-large-fallback-batch.md), which established source batching and fallback retry behavior. This slice preserves those behaviors and adds type validation for the two batch-size controls.

No upstream issue was filed from this local workspace.

## Changes

- Add a small `SitePagesAccessor` helper for positive integer controls.
- Reject non-integer `source_batch_size` values with `ValueError("source_batch_size must be an integer")`.
- Reject non-integer `fallback_batch_size` values with `ValueError("fallback_batch_size must be an integer")`.
- Preserve existing `source_batch_size <= 0` and `fallback_batch_size <= 0` `ValueError` messages.
- Preserve existing source iterator search order, source chunking, fallback retry, per-page failure, result-field, and required-tag filtering behavior.

## Type Of Change

- Input validation
- Public API behavior hardening
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `Site.pages.iter_sources(source_batch_size=...)` must reject non-integer source batch sizes with `ValueError("source_batch_size must be an integer")` before search, primary source fetches, or chunk comparison logic begins. |
| R2 | `Site.pages.iter_sources(fallback_batch_size=...)` must reject non-integer fallback batch sizes with `ValueError("fallback_batch_size must be an integer")` before search, primary source fetches, fallback source fetches, or fallback `range(...)` traversal begins. |
| R3 | Existing positive integer batch-size behavior must remain unchanged for primary source chunking and fallback retry chunking. |
| R4 | Existing non-positive batch-size behavior must remain unchanged: `source_batch_size <= 0` and `fallback_batch_size <= 0` raise their existing `ValueError(... must be greater than 0)` messages. |
| R5 | Existing `iter_sources(...)`, `iter_search(...)`, required-tag filtering, source fallback, result context fields, and ListPages behavior must remain unchanged. |
| R6 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R7 | Focused RED/GREEN, adjacent search/source iterator tests, broader unit tests, lint, format, type, and whitespace gates must pass before claiming this local implementation complete; unavailable tools must be reported instead of hidden. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | String and float source batch sizes fail with a stable `ValueError` before any ListPages search. | New `TestSitePagesAccessor.test_iter_sources_source_batch_size_must_be_integer` failed RED before the fix with raw `TypeError` for `"2"` and passed GREEN after it. | Leaking `TypeError`, accepting `"2"`, accepting `1.5`, coercing values, or calling `PageCollection.search_pages(...)` rejects this local completion claim. | Source iterator public API boundary | `src/wikidot/module/site.py`, `tests/unit/test_site.py` |
| R2 | String and float fallback batch sizes fail with a stable `ValueError` before any ListPages search. | New `TestSitePagesAccessor.test_iter_sources_fallback_batch_size_must_be_integer` failed RED before the fix with raw `TypeError` for `"1"` and passed GREEN after it. | Leaking `TypeError`, accepting `"1"`, accepting `1.5`, coercing values, calling `PageCollection.search_pages(...)`, or reaching fallback `range(...)` rejects this local completion claim. | Source iterator public API boundary | `src/wikidot/module/site.py`, `tests/unit/test_site.py` |
| R3 | Valid positive integer source and fallback batch sizes preserve existing chunking and retry behavior. | `TestSitePagesAccessor` passed 16 tests; adjacent page/search/source tests passed 211 tests. | Changing result order, primary source batch sizes, fallback retry chunks, missing-page retry behavior, or per-page failure records rejects this local completion claim. | Source iterator chunking and fallback | `tests/unit/test_site.py`, `tests/unit/test_page.py`, `tests/unit/test_search_pages_query.py` |
| R4 | Existing non-positive batch-size range checks remain compatible. | `TestSitePagesAccessor` and full unit tests passed after the helper replaced the inline checks. | Changing `source_batch_size <= 0` or `fallback_batch_size <= 0` messages or acceptance behavior rejects this local completion claim. | Source iterator validation | `src/wikidot/module/site.py`, `tests/unit/test_site.py` |
| R5 | Existing search, required-tag, source result, ListPages, and page module behavior remains green. | Full unit passed 926 tests. | Regressing `iter_search(...)`, `iter_sources(...)`, required-tag filtering, source fallback, source result fields, search pagination validation, tag-list validation, parent-fullname validation, ListPages parsing, or page collection behavior rejects this local completion claim. | Page/source collection workflows | `tests/unit` |
| R6 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level tests only. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, or live Wikidot actions rejects this local completion claim. | Test and draft privacy | this draft |
| R7 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, source iterator class tests passed, adjacent page/search/source tests passed, full unit passed, ruff, format, mypy, and whitespace checks passed; pyright was unavailable. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `7890d77 fix(site): validate source iterator batch sizes`.

- RED: `uv run --extra test pytest tests/unit/test_site.py::TestSitePagesAccessor::test_iter_sources_source_batch_size_must_be_integer tests/unit/test_site.py::TestSitePagesAccessor::test_iter_sources_fallback_batch_size_must_be_integer -q` failed before the fix. `source_batch_size="2"` and `fallback_batch_size="1"` leaked raw comparison `TypeError` from the existing `<= 0` checks.
- GREEN: `uv run --extra test pytest tests/unit/test_site.py::TestSitePagesAccessor::test_iter_sources_source_batch_size_must_be_integer tests/unit/test_site.py::TestSitePagesAccessor::test_iter_sources_fallback_batch_size_must_be_integer -q` passed 2 tests.
- `uv run --extra test pytest tests/unit/test_site.py::TestSitePagesAccessor -q` passed 16 tests.
- `uv run --extra test pytest tests/unit/test_site.py::TestSitePagesAccessor tests/unit/test_page.py tests/unit/test_search_pages_query.py -q` passed 211 tests.
- `uv run ruff format src tests` left 80 files unchanged.
- `uv run --extra test pytest tests/unit -q` passed 926 tests.
- `uv run ruff check` passed.
- `uv run ruff format --check` passed with 80 files already formatted.
- `uv run mypy src tests` passed with no issues in 80 source files.
- `git diff --check` passed.

Not run successfully: `uv run pyright src tests` failed because this environment could not spawn a `pyright` executable.

## Acceptance Criteria

- `Site.pages.iter_sources(source_batch_size="2")` raises `ValueError("source_batch_size must be an integer")` before calling `PageCollection.search_pages(...)`.
- `Site.pages.iter_sources(source_batch_size=1.5)` raises `ValueError("source_batch_size must be an integer")` before calling `PageCollection.search_pages(...)`.
- `Site.pages.iter_sources(fallback_batch_size="1")` raises `ValueError("fallback_batch_size must be an integer")` before calling `PageCollection.search_pages(...)`.
- `Site.pages.iter_sources(fallback_batch_size=1.5)` raises `ValueError("fallback_batch_size must be an integer")` before calling `PageCollection.search_pages(...)`.
- Existing positive integer source/fallback batching behavior is unchanged.
- Existing non-positive source/fallback batch-size validation remains unchanged.
- Existing search, source iterator, required-tag, fallback retry, source result, and ListPages tests remain green.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

Source iterator batch sizes are control-plane values for chunked source retrieval and fallback retries. Invalid types should fail at the iterator boundary with stable caller-facing validation rather than leaking Python comparison errors, silently accepting floats, or deferring failure until source collection has already started.

## Local Evidence, Not For Upstream Paste

- Local rollout evidence used bounded ListPages and source iterator workflows with explicit source/fallback batch sizes and per-page source failure records.
- Existing local drafts covered source iterator creation, fallback retry behavior, large fallback chunks, result ledger fields, required-tag filtering, response-body diagnostics, and pagination type validation, but did not cover non-integer `iter_sources(...)` batch-size controls.
- The focused RED failures showed string batch sizes leaking raw `TypeError` from the range checks; the added tests also cover float values so they cannot be accepted into chunking or fallback traversal.
- This slice only validates source iterator batch-size types; it does not change valid source batching, fallback retry order, missing-page retry policy, per-page error reporting, result ledger fields, ListPages search, required-tag filtering, live site behavior, or parsing.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw login response bodies, and private site data out of upstream discussion.

## Additional Notes

The change intentionally rejects malformed batch-size types instead of coercing them. Callers that load source iterator batch sizes from CLI arguments, environment variables, or config files should parse those values into integers before calling `Site.pages.iter_sources(...)`.
