# PR Draft: Validate Source Result Outcomes

## Summary

`PageSourceResult` is the ledger-friendly result object yielded by `Site.pages.iter_sources(...)`, but direct dataclass construction accepted malformed `source` and `error` fields. A caller could construct `PageSourceResult(source="source", error=NotFoundException(...))`, which stored a non-`PageSource` object as source state, or construct `PageSourceResult(source=None, error="missing")`, which exported `"str"` as an error type even though source-result errors should be real exceptions. It also allowed ambiguous outcomes: `source=None, error=None` produced a failed row with no diagnostic, while `source=PageSource(...), error=NotFoundException(...)` produced a contradictory row with `ok=False` and non-empty `wiki_text`.

This change validates `PageSourceResult` at initialization. `source` now accepts only `PageSource` or `None`, `error` accepts only `Exception` or `None`, and each result must describe exactly one outcome: either a successful source or a failure exception. Existing source iterator result generation, fallback behavior, page/site/fullname/page_id properties, `wiki_text`, `error_type`, `error_message`, and `as_dict()` output for valid results remain unchanged.

## Outcome

Callers cannot silently create malformed source-result ledger rows through the public constructor, while existing source collection and source-result audit exports remain intact.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use `Site.pages.iter_sources(...)`, direct `PageSourceResult(...)` construction in tests or local ledgers, large page-source collection, source retry ledgers, translation workflows, generated page inventories, migration scripts, archival jobs, or source collection audit rows.

## Current Evidence

Local rollout-backed drafts repeatedly identify page-source collection and source-result ledgers as practical workflow surfaces. Existing drafts [004-feature-large-corpus-page-source-collection.md](004-feature-large-corpus-page-source-collection.md), [019-pr-page-source-iterator-fallback.md](019-pr-page-source-iterator-fallback.md), [025-pr-source-result-error-page-context.md](025-pr-source-result-error-page-context.md), [026-pr-source-iterator-parse-failure-isolation.md](026-pr-source-iterator-parse-failure-isolation.md), [027-pr-source-result-wiki-text.md](027-pr-source-result-wiki-text.md), [049-pr-filter-iterators-by-required-tags.md](049-pr-filter-iterators-by-required-tags.md), [051-pr-preserve-source-batch-successes.md](051-pr-preserve-source-batch-successes.md), [052-pr-source-result-context-properties.md](052-pr-source-result-context-properties.md), [069-pr-source-result-ledger-record.md](069-pr-source-result-ledger-record.md), [147-pr-source-result-error-type.md](147-pr-source-result-error-type.md), [195-pr-source-iterator-site-context.md](195-pr-source-iterator-site-context.md), [225-pr-source-result-page-id-ledger.md](225-pr-source-result-page-id-ledger.md), [338-pr-result-ledger-site-field.md](338-pr-result-ledger-site-field.md), [345-pr-validate-source-iterator-batch-sizes.md](345-pr-validate-source-iterator-batch-sizes.md), and [411-pr-reject-boolean-source-iterator-batch-sizes.md](411-pr-reject-boolean-source-iterator-batch-sizes.md) establish source iteration, fallback retries, per-page failure isolation, source-result fields, and source-result ledger exports as active operational boundaries.

Those prior slices are not duplicates. They covered iterator behavior, source acquisition, fallback failures, parser isolation, context fields, dictionary exports, and iterator controls. None of them validates direct `PageSourceResult(...)` construction before malformed `source` or `error` values become stored frozen dataclass state. This slice also follows the direct result-object hardening pattern from [428-pr-validate-publish-result-status-fields.md](428-pr-validate-publish-result-status-fields.md), but applies it to source-result success/failure state instead of publish-result status fields.

## Related Issue

Builds directly on [019-pr-page-source-iterator-fallback.md](019-pr-page-source-iterator-fallback.md), [027-pr-source-result-wiki-text.md](027-pr-source-result-wiki-text.md), [052-pr-source-result-context-properties.md](052-pr-source-result-context-properties.md), [069-pr-source-result-ledger-record.md](069-pr-source-result-ledger-record.md), [147-pr-source-result-error-type.md](147-pr-source-result-error-type.md), [195-pr-source-iterator-site-context.md](195-pr-source-iterator-site-context.md), [225-pr-source-result-page-id-ledger.md](225-pr-source-result-page-id-ledger.md), [338-pr-result-ledger-site-field.md](338-pr-result-ledger-site-field.md), and [428-pr-validate-publish-result-status-fields.md](428-pr-validate-publish-result-status-fields.md).

No upstream issue was filed from this local workspace.

## Changes

- Add `PageSourceResult.__post_init__()` validation.
- Reject malformed `source` values with `ValueError("source must be PageSource or None")`.
- Reject malformed `error` values with `ValueError("error must be an Exception or None")`.
- Reject ambiguous success/failure state with `ValueError("source and error must describe exactly one outcome")`.
- Preserve valid success results with `source=PageSource(...)` and `error=None`.
- Preserve valid failure results with `source=None` and `error=Exception(...)`.
- Preserve existing source iterator ordering, fallback behavior, per-page failures, page/site/fullname/page_id properties, `wiki_text`, `error_type`, `error_message`, and `as_dict()` output for valid results.

## Type Of Change

- Input validation
- Public dataclass constructor behavior hardening
- Source-result ledger state integrity
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `PageSourceResult(source=...)` must reject non-`PageSource` non-`None` values with `ValueError("source must be PageSource or None")` before storing result state. |
| R2 | `PageSourceResult(error=...)` must reject non-`Exception` non-`None` values with `ValueError("error must be an Exception or None")` before storing result state. |
| R3 | `PageSourceResult(source=None, error=None)` and `PageSourceResult(source=PageSource(...), error=Exception(...))` must raise `ValueError("source and error must describe exactly one outcome")`. |
| R4 | Valid source successes and valid source failures must preserve existing result properties and ledger dictionaries. |
| R5 | Existing `Site.pages.iter_sources(...)`, fallback retries, per-page source failures, source result ordering, page search, publish-result behavior, and adjacent site/page behavior must remain unchanged. |
| R6 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private user data, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R7 | Focused RED/GREEN, source-result tests, adjacent site/page/search tests, full unit tests, lint, format, type, and whitespace gates must pass before claiming this local implementation complete; unavailable tools must be reported instead of hidden. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Malformed source values fail at the public dataclass boundary. | `TestSitePagesAccessor.test_source_result_rejects_malformed_source` failed RED for `"source"`, `True`, and `object()`, then passed GREEN after `PageSourceResult.__post_init__()` source validation was added. | Accepting strings, booleans, arbitrary objects, or other non-`PageSource` source values rejects this local completion claim. | PageSourceResult constructor | `src/wikidot/module/site.py`, `tests/unit/test_site.py` |
| R2 | Malformed error values fail at the public dataclass boundary. | `TestSitePagesAccessor.test_source_result_rejects_malformed_error` failed RED for `"missing"`, `True`, and `object()`, then passed GREEN after error validation was added. | Accepting strings, booleans, arbitrary objects, or exporting non-exception `error_type` values rejects this local completion claim. | PageSourceResult constructor | `src/wikidot/module/site.py`, `tests/unit/test_site.py` |
| R3 | Ambiguous result state fails before object construction completes. | `TestSitePagesAccessor.test_source_result_rejects_ambiguous_outcomes` failed RED for both missing and double-populated outcomes, then passed GREEN after the exclusive outcome check was added. | Returning `ok=False` with no error, returning `ok=False` with `wiki_text`, or storing both source and failure state rejects this local completion claim. | PageSourceResult constructor | `src/wikidot/module/site.py`, `tests/unit/test_site.py` |
| R4 | Valid source-result semantics stay green. | Existing `test_source_result_page_id_does_not_trigger_lookup` and `test_iter_sources_result_exports_ledger_record` passed with the new constructor validation. | Triggering lazy page-ID lookup, changing `site`, `fullname`, `page_id`, `ok`, `wiki_text`, `error_type`, `error_message`, `as_dict()` keys, or row ordering rejects this local completion claim. | PageSourceResult properties and ledger export | `tests/unit/test_site.py` |
| R5 | Existing source and adjacent workflows remain green. | `TestSitePagesAccessor` passed 28 tests; `TestSitePagesAccessor` plus `TestSitePageAccessor` passed 88 tests; `tests/unit/test_site.py tests/unit/test_page.py tests/unit/test_search_pages_query.py` passed 471 tests; full unit tests passed 1614 tests. | Regressing source iterator batching, fallback retries, per-page failure isolation, source result ordering, page search, search pagination, required-tag filtering, publish result behavior, or page workflows rejects this local completion claim. | Site/page/source workflows | `tests/unit/test_site.py`, `tests/unit/test_page.py`, `tests/unit/test_search_pages_query.py`, `tests/unit` |
| R6 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level tests only. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, private user data, page source text, forum source text, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R7 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, targeted source-result and adjacent tests passed, full unit passed, ruff, format, mypy, and whitespace checks passed; pyright was unavailable. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `f55a86b fix(site): validate source result outcomes`.

- RED: `uv run pytest tests/unit/test_site.py::TestSitePagesAccessor::test_source_result_rejects_malformed_source -q` failed 3 tests before the source-type fix; every malformed `source` value reported `DID NOT RAISE`.
- GREEN: `uv run pytest tests/unit/test_site.py::TestSitePagesAccessor::test_source_result_rejects_malformed_source -q` passed 3 tests after adding `source` validation.
- RED: `uv run pytest tests/unit/test_site.py::TestSitePagesAccessor::test_source_result_rejects_malformed_error tests/unit/test_site.py::TestSitePagesAccessor::test_source_result_rejects_ambiguous_outcomes -q` failed 5 tests before error/outcome validation; every malformed `error` or ambiguous state reported `DID NOT RAISE`.
- GREEN: `uv run pytest tests/unit/test_site.py::TestSitePagesAccessor::test_source_result_rejects_malformed_source tests/unit/test_site.py::TestSitePagesAccessor::test_source_result_rejects_malformed_error tests/unit/test_site.py::TestSitePagesAccessor::test_source_result_rejects_ambiguous_outcomes tests/unit/test_site.py::TestSitePagesAccessor::test_source_result_page_id_does_not_trigger_lookup tests/unit/test_site.py::TestSitePagesAccessor::test_iter_sources_result_exports_ledger_record -q` passed 10 tests.
- `uv run ruff format src/wikidot/module/site.py tests/unit/test_site.py` left 2 files unchanged.
- `uv run mypy src/wikidot/module/site.py tests/unit/test_site.py` passed with no issues in 2 source files.
- `uv run pytest tests/unit/test_site.py::TestSitePagesAccessor -q` passed 28 tests.
- `uv run pytest tests/unit/test_site.py::TestSitePagesAccessor tests/unit/test_site.py::TestSitePageAccessor -q` passed 88 tests.
- `uv run pytest tests/unit/test_site.py tests/unit/test_page.py tests/unit/test_search_pages_query.py -q` passed 471 tests.
- `uv run ruff check` passed.
- `uv run ruff format --check` passed with 81 files already formatted.
- `uv run mypy src tests` passed with no issues in 81 source files.
- `git diff --check` passed.
- `uv run pytest tests/unit -q` passed 1614 tests.

Not run successfully: `uv run pyright src tests` failed because this environment could not spawn a `pyright` executable.

## Acceptance Criteria

- `PageSourceResult(source="source", error=NotFoundException("missing"))`, `source=True`, and `source=object()` raise `ValueError("source must be PageSource or None")`.
- `PageSourceResult(source=None, error="missing")`, `error=True`, and `error=object()` raise `ValueError("error must be an Exception or None")`.
- `PageSourceResult(source=None, error=None)` and `PageSourceResult(source=PageSource(...), error=NotFoundException(...))` raise `ValueError("source and error must describe exactly one outcome")`.
- Valid `PageSourceResult(source=PageSource(...), error=None)` and `PageSourceResult(source=None, error=Exception(...))` continue to work.
- Existing `PageSourceResult.page_id` remains side-effect-free and does not trigger lazy page-ID acquisition.
- Existing `PageSourceResult.as_dict()` output remains unchanged for valid source iterator rows.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private user data, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

`PageSourceResult` is the durable object shape behind large source-collection audit ledgers. Constructor validation keeps malformed local success/failure state out of result records while preserving the existing `Site.pages.iter_sources(...)` path that constructs either a successful `PageSource` row or a failure `Exception` row.

## Local Evidence, Not For Upstream Paste

- Local rollout evidence used large page-source collection, fallback source retries, per-page source failures, source-result context fields, page IDs, site fields, and source-result audit dictionaries.
- Existing local drafts covered source iteration, retry/fallback behavior, result ordering, parser failure isolation, source text fields, source-result context, error type/message fields, page/site/page_id ledger fields, and iterator control validation, but did not cover direct `PageSourceResult(...)` source/error construction.
- The focused RED failures showed malformed constructor values and ambiguous source/error state were accepted as frozen dataclass state. The GREEN regressions cover malformed `source`, malformed `error`, ambiguous outcomes, valid side-effect-free `page_id`, valid audit dictionaries, source iterator behavior, site/page/search workflows, and full unit behavior.
- This slice only validates source-result outcome fields. It does not change ListPages discovery, source request construction, retry counts, fallback batch sizing, parse-failure handling, source caching, source text extraction, page ID lookup behavior, publish behavior, live site behavior, or parser behavior.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw login response bodies, private user data, page source text, forum source text, and private site data out of upstream discussion.

## Additional Notes

The change intentionally rejects stand-in strings and generic objects for source-result errors. Callers loading source-result records from JSON, YAML, CLI flags, spreadsheets, generated structures, or ledgers should reconstruct successful rows with `PageSource` objects and failure rows with real `Exception` instances before using `PageSourceResult`.
