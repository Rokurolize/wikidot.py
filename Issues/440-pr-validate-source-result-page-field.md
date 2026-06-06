# PR Draft: Validate Source Result Page Field

## Summary

`PageSourceResult` is the ledger-friendly result object yielded by `Site.pages.iter_sources(...)`. Issue 429 validated direct `source` and `error` construction, but the public constructor still accepted malformed `page` values such as `None`, booleans, strings, dictionaries, and arbitrary objects. Those malformed values could become frozen result state and later break `site`, `fullname`, `page_id`, or `as_dict()` access outside the constructor boundary.

This change validates `PageSourceResult.page` at initialization. Malformed values now raise `ValueError("page must be a Page")`. Existing source iterator result generation, source/error outcome validation, side-effect-free `page_id`, `wiki_text`, `error_type`, `error_message`, and `as_dict()` output for valid results remain unchanged.

## Outcome

Callers cannot silently create malformed source-result ledger objects with non-`Page` parent state, while existing source collection and valid `PageSourceResult(...)` rows remain intact.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use `Site.pages.iter_sources(...)`, direct `PageSourceResult(...)` construction in tests or local ledgers, large source collection, retry ledgers, migration scripts, archival jobs, generated page inventories, source comparison tooling, or audit-row exports.

## Current Evidence

Local rollout-backed drafts repeatedly identify large source collection and source-result ledgers as practical workflow surfaces. Existing drafts [019-pr-page-source-iterator-fallback.md](019-pr-page-source-iterator-fallback.md), [025-pr-source-result-error-page-context.md](025-pr-source-result-error-page-context.md), [026-pr-source-iterator-parse-failure-isolation.md](026-pr-source-iterator-parse-failure-isolation.md), [027-pr-source-result-wiki-text.md](027-pr-source-result-wiki-text.md), [052-pr-source-result-context-properties.md](052-pr-source-result-context-properties.md), [069-pr-source-result-ledger-record.md](069-pr-source-result-ledger-record.md), [195-pr-source-iterator-site-context.md](195-pr-source-iterator-site-context.md), [225-pr-source-result-page-id-ledger.md](225-pr-source-result-page-id-ledger.md), [338-pr-result-ledger-site-field.md](338-pr-result-ledger-site-field.md), and [429-pr-validate-source-result-outcomes.md](429-pr-validate-source-result-outcomes.md) establish source iterator ordering, failure isolation, page/site/fullname/page_id ledger fields, source/error validation, and durable source-result exports as active operational boundaries.

Those prior slices are not duplicates. They covered source fetching, fallback behavior, parser failure isolation, result text/error fields, site/fullname/page_id exports, and direct `source`/`error` outcome validation. None validates direct `PageSourceResult(page=...)` construction before malformed page state becomes stored dataclass state.

## Related Issue

Builds directly on [019-pr-page-source-iterator-fallback.md](019-pr-page-source-iterator-fallback.md), [052-pr-source-result-context-properties.md](052-pr-source-result-context-properties.md), [069-pr-source-result-ledger-record.md](069-pr-source-result-ledger-record.md), [195-pr-source-iterator-site-context.md](195-pr-source-iterator-site-context.md), [225-pr-source-result-page-id-ledger.md](225-pr-source-result-page-id-ledger.md), [338-pr-result-ledger-site-field.md](338-pr-result-ledger-site-field.md), and [429-pr-validate-source-result-outcomes.md](429-pr-validate-source-result-outcomes.md).

No upstream issue was filed from this local workspace.

## Changes

- Add `PageSourceResult.page` validation.
- Reject non-`Page` values with `ValueError("page must be a Page")`.
- Validate `page` before `source`, `error`, and exclusive-outcome checks so the constructor reports the malformed wrapped page first.
- Preserve existing `PageSourceResult.source`, `error`, outcome, `ok`, `site`, `fullname`, `page_id`, `wiki_text`, `error_type`, `error_message`, and `as_dict()` behavior for valid result rows.
- Preserve `Site.pages.iter_sources(...)` discovery, batching, fallback retry behavior, source parse-failure isolation, row ordering, and ledger exports.

## Type Of Change

- Input validation
- Public dataclass constructor behavior hardening
- Source-result ledger parent-state integrity

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `PageSourceResult(page=None)`, `True`, `"test-page"`, `{"fullname": "test-page"}`, and `object()` must raise `ValueError("page must be a Page")` before storing result state when `source`/`error` describe an otherwise valid failure row. |
| R2 | Valid `Page` instances must remain valid and preserve existing source-result fields and ledger exports. |
| R3 | Existing `PageSourceResult.source`, `error`, and exclusive-outcome validation must remain unchanged. |
| R4 | Existing `Site.pages.iter_sources(...)` discovery, source batching, fallback behavior, per-page failures, source-result ordering, side-effect-free `page_id`, and adjacent site workflows must remain unchanged. |
| R5 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private user data, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R6 | Focused RED/GREEN, source-result tests, site tests, full unit tests, lint, format, mypy, source-file pyright, and whitespace gates must pass before claiming this local implementation complete; broad pyright limitations must be reported instead of hidden. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Malformed constructor pages fail at the public dataclass boundary. | `TestSitePagesAccessor.test_source_result_rejects_malformed_pages` failed RED for 5 malformed values because the constructor did not raise, then passed GREEN after page validation was added. | Accepting missing values, booleans, strings, dictionaries, arbitrary objects, or emitting source-result rows with non-`Page` parent state rejects this local completion claim. | PageSourceResult constructor | `src/wikidot/module/site.py`, `tests/unit/test_site.py` |
| R2 | Valid page semantics stay green. | Existing valid source-result context, page ID, ledger export, source iterator, site tests, and full unit tests passed after the validator was added. | Rejecting valid `Page` instances, changing `site`, `fullname`, `page_id`, `wiki_text`, `error_type`, `error_message`, `ok`, or `as_dict()` for valid rows rejects this local completion claim. | PageSourceResult properties and ledger export | `tests/unit/test_site.py`, `tests/unit` |
| R3 | Existing direct source-result validators stay intact. | Focused GREEN included malformed `source`, malformed `error`, ambiguous outcome, side-effect-free `page_id`, and audit dictionary coverage. | Weakening Issue 429 behavior, accepting malformed source/error values, accepting missing or double-populated outcomes, or changing diagnostics rejects this local completion claim. | PageSourceResult constructor | `tests/unit/test_site.py` |
| R4 | Existing source iterator and adjacent site workflows remain green. | `tests/unit/test_site.py::TestSitePagesAccessor` passed 33 tests, `tests/unit/test_site.py` passed 241 tests, and full unit tests passed 1687 tests. | Regressing source search discovery, batched source fetches, fallback retries, parser failure isolation, result ordering, per-page failure rows, source text exports, page ID exports, or adjacent site workflows rejects this local completion claim. | Source iterator and adjacent site workflows | `tests/unit/test_site.py`, `tests/unit` |
| R5 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level tests only. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, private user data, page source text, forum source text, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R6 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, source-result tests passed, site tests passed, full unit passed, ruff, format, mypy, source-file pyright, and whitespace checks passed; broad pyright was run and reported existing full-tree typing issues unrelated to this slice. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `9fca012 fix(site): validate source result page`.

- RED: `uv run pytest tests/unit/test_site.py::TestSitePagesAccessor::test_source_result_rejects_malformed_pages -q` failed 5 tests before the fix; every malformed `page` value reported `DID NOT RAISE`.
- GREEN: `uv run pytest tests/unit/test_site.py::TestSitePagesAccessor::test_source_result_rejects_malformed_pages tests/unit/test_site.py::TestSitePagesAccessor::test_source_result_rejects_malformed_source tests/unit/test_site.py::TestSitePagesAccessor::test_source_result_rejects_malformed_error tests/unit/test_site.py::TestSitePagesAccessor::test_source_result_rejects_ambiguous_outcomes tests/unit/test_site.py::TestSitePagesAccessor::test_source_result_page_id_does_not_trigger_lookup tests/unit/test_site.py::TestSitePagesAccessor::test_iter_sources_result_exports_ledger_record -q` passed 15 tests.
- `uv run pytest tests/unit/test_site.py::TestSitePagesAccessor -q` passed 33 tests.
- `uv run pytest tests/unit/test_site.py -q` passed 241 tests.
- `uv run pytest tests/unit -q` passed 1687 tests.
- `uv run ruff check src/wikidot/module/site.py tests/unit/test_site.py` passed.
- `uv run ruff check` passed.
- `uv run ruff format --check` passed with 82 files already formatted.
- `uv run mypy src tests` passed with no issues in 82 source files.
- `uv run pyright src/wikidot/module/site.py` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

Not used as a completion blocker: `uv run pyright src tests` ran but failed with 114 existing full-tree typing errors, including intentional invalid-input test fixtures, fixture `None` mismatches, invalid `test_search_pages_query` parameter calls, and one unrelated BeautifulSoup narrowing warning in `src/wikidot/module/forum_post.py`. The changed source file passes pyright.

## Acceptance Criteria

- `PageSourceResult(page=None)`, `True`, `"test-page"`, `{"fullname": "test-page"}`, and `object()` raise `ValueError("page must be a Page")`.
- Valid `Page` instances remain valid as `page`.
- Existing `source`, `error`, and exclusive-outcome validation remains unchanged.
- Existing `site`, `fullname`, `page_id`, `wiki_text`, `error_type`, `error_message`, `ok`, and `as_dict()` behavior remains unchanged for valid rows.
- Existing `Site.pages.iter_sources(...)`, source batching, fallback retry behavior, parse-failure isolation, row ordering, per-page failure rows, source text exports, and page ID exports remain green.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private user data, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

`PageSourceResult.page` is the parent context behind large source collection, retry ledgers, source audit exports, generated page inventories, and migration checks. Constructor validation keeps malformed local parent-page state out of source-result records while preserving the existing iterator path that constructs results from real `Page` objects.

## Local Evidence, Not For Upstream Paste

- Local rollout evidence used large source collection, source iterator fallback, source-result context fields, page/site/fullname/page_id ledger exports, and direct source-result construction.
- Existing local drafts covered source iterator fetch/fallback behavior, parser failure isolation, failure messages, `wiki_text`, `fullname`, `error_message`, `error_type`, `site`, `page_id`, `as_dict()`, and direct `source`/`error` outcome validation, but did not cover direct `PageSourceResult(page=...)` construction.
- The focused RED failures showed invalid constructor page fields were accepted as dataclass state. The GREEN regressions cover missing, boolean, string, dictionary, and arbitrary object page values, plus direct constructor validators and source iterator behavior.
- This slice only validates source-result parent-page constructor input. It does not change source discovery, source fetch request construction, fallback batch sizing, source parse-failure isolation, row ordering, source text extraction, failure exception construction, page-ID lookup behavior, live site behavior, or request helper behavior.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw login response bodies, private user data, page source text, forum source text, and private site data out of upstream discussion.

## Additional Notes

The change intentionally validates only that `page` is a `Page` instance. It does not validate page IDs, page fullnames, site identity, cached source state, or client authentication at `PageSourceResult` construction time; those are separate page object and source collection concerns.
