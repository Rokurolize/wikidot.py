# PR Draft: Validate Source Result Source Ownership

## Summary

`PageSourceResult` is the ledger-friendly result object yielded by `Site.pages.iter_sources(...)` and also useful for direct tests, generated source ledgers, retry rows, and rehydrated audit records. Issue 429 validated direct `source` and `error` shape plus exclusive outcome state, Issue 440 validated that `page` is a real `Page`, and Issue 430 validated `PageSource.wiki_text`. One ownership gap remained: callers could construct `PageSourceResult(page=page_one, source=PageSource(page_two, ...))`. The row looked successful and exported `fullname` from `page_one`, but `wiki_text` came from a `PageSource` whose retained owner described another page.

This change validates successful source-result ownership during `PageSourceResult.__post_init__` after existing page/source/error/outcome checks. When `source` is present, the retained `source.page` must describe the result `page` by the same retained `Site` object and compatible page identity: matching page IDs when both sides have IDs, otherwise matching `fullname`. Mismatches raise `ValueError("source must belong to the result page")` before the malformed result row is stored. Valid same-page source rows, same-logical-page source wrappers, failed rows with `source=None`, malformed page/source/error diagnostics, outcome diagnostics, source iterator result generation, and ledger exports remain unchanged.

## Outcome

Directly constructed source-result rows cannot combine one result page with another page's retained source wrapper while still reporting `ok=True`.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use `Site.pages.iter_sources(...)`, direct `PageSourceResult(...)` construction in tests or local ledgers, large source collection, retry ledgers, migration scripts, archival jobs, generated page inventories, source comparison tooling, or audit-row exports.

## Current Evidence

Local source-result drafts establish the surrounding behavior. [019-pr-page-source-iterator-fallback.md](019-pr-page-source-iterator-fallback.md), [025-pr-source-result-error-page-context.md](025-pr-source-result-error-page-context.md), [026-pr-source-iterator-parse-failure-isolation.md](026-pr-source-iterator-parse-failure-isolation.md), [027-pr-source-result-wiki-text.md](027-pr-source-result-wiki-text.md), [052-pr-source-result-context-properties.md](052-pr-source-result-context-properties.md), [069-pr-source-result-ledger-record.md](069-pr-source-result-ledger-record.md), [147-pr-source-result-error-type.md](147-pr-source-result-error-type.md), [195-pr-source-iterator-site-context.md](195-pr-source-iterator-site-context.md), [225-pr-source-result-page-id-ledger.md](225-pr-source-result-page-id-ledger.md), and [338-pr-result-ledger-site-field.md](338-pr-result-ledger-site-field.md) make source-result rows a practical durable ledger surface. [429-pr-validate-source-result-outcomes.md](429-pr-validate-source-result-outcomes.md) validates result `source`, `error`, and exclusive outcome state. [440-pr-validate-source-result-page-field.md](440-pr-validate-source-result-page-field.md) validates the result page field and explicitly leaves page IDs, page fullnames, site identity, and cached source state outside scope. [600-pr-validate-page-source-cache-ownership.md](600-pr-validate-page-source-cache-ownership.md) and [601-pr-validate-page-revision-source-cache-ownership.md](601-pr-validate-page-revision-source-cache-ownership.md) validate adjacent `PageSource` cache ownership boundaries, but they do not validate direct source-result row construction.

## Related Issue / Non-Duplicate Analysis

This is not a duplicate of Issue 429. Issue 429 rejects non-`PageSource` source values, non-`Exception` errors, and ambiguous success/failure state; it does not validate whether a valid `PageSource` belongs to the result page.

This is not a duplicate of Issue 440. Issue 440 validates that `PageSourceResult.page` is a `Page` instance and explicitly does not validate page identity, site identity, or cached source state.

This is not a duplicate of Issue 430. Issue 430 validates that `PageSource.wiki_text` is a string; it deliberately avoids changing `PageSource.page` construction semantics.

This is not a duplicate of Issues 600 or 601. Those slices validate direct `Page.source` and `PageRevision.source` cache slots, not source-result ledger rows.

No upstream issue was filed from this local workspace.

## Changes

- Add `PageSourceResult` source ownership validation for successful direct construction.
- Reject `PageSource` values whose retained `source.page` does not describe the result `page`.
- Preserve existing `page`, `source`, `error`, and exclusive-outcome validation order and diagnostics.
- Preserve failed source-result rows with `source=None` and a real `Exception`.
- Preserve valid same-page and same-logical-page source wrappers.
- Preserve `Site.pages.iter_sources(...)` discovery, batching, fallback retry behavior, parser failure isolation, row ordering, and ledger exports.

## Type Of Change

- Input validation
- Public dataclass constructor behavior hardening
- Source-result ledger ownership integrity
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `PageSourceResult(page=page_one, source=PageSource(page_two, ...))` must reject the different retained source page with `ValueError("source must belong to the result page")` before storing successful result state. |
| R2 | `PageSourceResult(page=page, source=PageSource(same_logical_page, ...))` must remain valid when both pages retain the same `Site` object and compatible page identity. |
| R3 | Existing malformed `page`, malformed `source`, malformed `error`, and ambiguous outcome diagnostics from Issues 429 and 440 must remain unchanged. |
| R4 | Existing failed rows with `source=None`, side-effect-free `page_id`, `wiki_text`, `error_type`, `error_message`, `as_dict()`, and source iterator generation must remain unchanged. |
| R5 | Existing page/source/revision/search/site workflows must remain unchanged. |
| R6 | The draft and tests must not require live Wikidot actions, credentials, cookies, auth JSON, raw rollout paths, pushes, upstream Issues, or upstream PRs. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Wrong-page successful source-result rows fail at the public constructor boundary. | `TestSitePagesAccessor.test_source_result_rejects_source_from_different_page` failed RED with `DID NOT RAISE`, then passed GREEN after `PageSourceResult.__post_init__` called the ownership preflight. | Accepting `PageSource(other_page, ...)`, returning `ok=True`, exporting `page_one.fullname` with `page_two` source text, or deferring the mismatch to later property access rejects this local completion claim. | `PageSourceResult` constructor | `src/wikidot/module/site.py`, `tests/unit/test_site.py` |
| R2 | Same-logical-page source wrappers remain valid. | `TestSitePagesAccessor.test_source_result_accepts_source_from_same_logical_page` passed with a distinct `Page` object sharing retained site, page ID, and fullname. | Requiring object identity rather than compatible page identity rejects valid duplicate/reconstructed same-page rows. | `PageSourceResult` constructor | `src/wikidot/module/site.py`, `tests/unit/test_site.py` |
| R3 | Existing constructor diagnostics stay stable. | Focused constructor validation passed 17 tests covering malformed page, malformed source, wrong-owner source, same-logical-page source, malformed error, ambiguous outcome, side-effect-free `page_id`, and ledger export. | Changing `ValueError("page must be a Page")`, `ValueError("source must be PageSource or None")`, `ValueError("error must be an Exception or None")`, or `ValueError("source and error must describe exactly one outcome")` rejects this local completion claim. | Source-result validation order | `tests/unit/test_site.py` |
| R4 | Existing source-result properties and iterator rows remain green. | `tests/unit/test_site.py` passed 284 tests. | Regressing source search discovery, batched source fetches, fallback retries, parser failure isolation, result ordering, per-page failure rows, source text exports, error exports, page ID exports, or audit dictionaries rejects this local completion claim. | Source iterator and result ledgers | `tests/unit/test_site.py` |
| R5 | Adjacent page/source/revision/search workflows remain green. | Adjacent site/page/page-source/page-revision/search coverage passed 751 tests, and full unit coverage passed 2726 tests. | Regressing direct page source caches, page revision source caches, search pagination/query behavior, source text validation, or adjacent page workflows rejects this local completion claim. | Page/source workflows | `tests/unit` |
| R6 | No live auth material or private site state is needed to prove the behavior. | The regressions use synthetic valid `Page`, `PageSource`, and `PageSourceResult` objects only, and this draft contains no credentials, cookies, auth JSON, raw response bodies, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. | Using real account names, credentials, cookies, auth JSON, sandbox details, raw rollout paths, pushes, upstream Issues, upstream PRs, live Wikidot actions, page source text from real sites, or private site data rejects this local completion claim. | Test and draft privacy | this draft |

## Testing

Implemented locally in commit `da9ae8c fix(site): validate source result source ownership`.

- RED: `uv run pytest tests/unit/test_site.py::TestSitePagesAccessor::test_source_result_rejects_source_from_different_page -q` failed before the fix with `DID NOT RAISE`.
- GREEN regression: `uv run pytest tests/unit/test_site.py::TestSitePagesAccessor::test_source_result_rejects_source_from_different_page -q` passed 1 test.
- Focused constructor coverage: `uv run pytest tests/unit/test_site.py::TestSitePagesAccessor::test_source_result_rejects_malformed_pages tests/unit/test_site.py::TestSitePagesAccessor::test_source_result_rejects_malformed_source tests/unit/test_site.py::TestSitePagesAccessor::test_source_result_rejects_source_from_different_page tests/unit/test_site.py::TestSitePagesAccessor::test_source_result_accepts_source_from_same_logical_page tests/unit/test_site.py::TestSitePagesAccessor::test_source_result_rejects_malformed_error tests/unit/test_site.py::TestSitePagesAccessor::test_source_result_rejects_ambiguous_outcomes tests/unit/test_site.py::TestSitePagesAccessor::test_source_result_page_id_does_not_trigger_lookup tests/unit/test_site.py::TestSitePagesAccessor::test_iter_sources_result_exports_ledger_record -q` passed 17 tests.
- Site coverage: `uv run pytest tests/unit/test_site.py -q` passed 284 tests.
- Adjacent site/page/source/revision/search coverage: `uv run pytest tests/unit/test_site.py tests/unit/test_page.py tests/unit/test_page_source.py tests/unit/test_page_revision.py tests/unit/test_search_pages_query.py -q` passed 751 tests.
- `uv run pytest tests/unit -q` passed 2726 tests.
- `uv run ruff format src/wikidot/module/site.py tests/unit/test_site.py` left 2 files unchanged.
- `uv run ruff check` passed.
- `uv run ruff format --check` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run pyright src tests` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `PageSourceResult(page=page_one, source=PageSource(page_two, "source"))` raises `ValueError("source must belong to the result page")` before storing successful result state.
- `PageSourceResult(page=page, source=PageSource(same_logical_page, "source"))` remains valid when both pages retain the same `Site` object and compatible page identity.
- Failed rows such as `PageSourceResult(page=page, source=None, error=NotFoundException("missing"))` remain valid.
- Existing malformed `page`, malformed `source`, malformed `error`, and ambiguous outcome diagnostics remain unchanged.
- Existing `ok`, `site`, `fullname`, `page_id`, `wiki_text`, `error_type`, `error_message`, and `as_dict()` behavior remains unchanged for valid rows.
- Existing `Site.pages.iter_sources(...)`, source batching, fallback retry behavior, parse-failure isolation, row ordering, per-page failure rows, source text exports, and page ID exports remain green.
- The new tests use unit-level synthetic values only and do not require live Wikidot, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

`PageSourceResult` rows are often persisted as source collection ledgers. A row whose public page identity and retained source owner disagree can export an internally contradictory successful record: page identity from one page, source text from another page's wrapper. Constructor ownership validation keeps successful rows internally coherent while preserving failure rows and existing iterator behavior.

## Local Evidence, Not For Upstream Paste

- The focused RED failure showed direct `PageSourceResult(page=page_one, source=PageSource(page_two, ...))` construction silently accepted a wrong-owner source wrapper.
- Existing local drafts covered source iteration, retry/fallback behavior, parser failure isolation, failure messages, `wiki_text`, `fullname`, `error_message`, `error_type`, `site`, `page_id`, `as_dict()`, direct `source`/`error` outcome validation, result page validation, page source cache ownership, and page revision source cache ownership, but did not validate that a successful source-result row's retained `PageSource` belongs to the result page.
- This slice only validates successful source-result source ownership during direct construction. It does not change source discovery, source fetch request construction, fallback batch sizing, source parse-failure isolation, row ordering, source text extraction, failure exception construction, page-ID lookup behavior, live site behavior, authentication semantics, or request helper behavior.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw login response bodies, page source text from real sites, and private site data out of upstream discussion.

## Additional Notes

The ownership check intentionally allows same-logical-page source wrappers because direct ledgers and tests may reconstruct the result `Page` and `PageSource.page` as distinct objects. The comparison therefore requires the same retained `Site` object and uses page IDs when both sides have them; if either side lacks an ID, it falls back to `fullname`. Different-site, different-ID, and different-fullname source evidence are rejected.
