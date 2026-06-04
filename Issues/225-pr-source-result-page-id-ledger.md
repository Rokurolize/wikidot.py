# PR Draft: Include Page IDs In Source Result Ledgers

## Summary

`Site.pages.iter_sources(...)` returns one `PageSourceResult` per page so large source-collection callers can persist successes, failures, and retry targets. The existing `PageSourceResult.as_dict()` ledger shape included `fullname`, `ok`, `wiki_text`, `error_type`, and `error_message`, but omitted the already-known numeric page ID. That made resumable ledgers weaker than publish result ledgers and forced callers to recover page IDs separately when deduplicating rows, retrying failed pages, or reconciling renamed/default-category pages.

This change adds a side-effect-free `PageSourceResult.page_id` property and includes `page_id` in `PageSourceResult.as_dict()`. The property reports the page ID already loaded on the `Page` object and returns `None` when it is not loaded; it does not call `Page.id` and therefore does not perform an implicit page-ID lookup during serialization.

## Related Issue

Builds on [004-feature-large-corpus-page-source-collection.md](004-feature-large-corpus-page-source-collection.md), [019-pr-page-source-iterator-fallback.md](019-pr-page-source-iterator-fallback.md), [025-pr-source-result-error-page-context.md](025-pr-source-result-error-page-context.md), [027-pr-source-result-wiki-text.md](027-pr-source-result-wiki-text.md), [052-pr-source-result-context-properties.md](052-pr-source-result-context-properties.md), [069-pr-source-result-ledger-record.md](069-pr-source-result-ledger-record.md), and [147-pr-source-result-error-type.md](147-pr-source-result-error-type.md). It also mirrors the page-ID precedent in [070-pr-publish-result-audit-record.md](070-pr-publish-result-audit-record.md), where publish-result ledgers already expose `page_id`.

No upstream issue was filed from this local workspace.

## Changes

- Add `PageSourceResult.page_id -> int | None`.
- Return the already-loaded `Page` ID without triggering lazy page-ID acquisition.
- Include `page_id` in `PageSourceResult.as_dict()`.
- Preserve existing `fullname`, `ok`, `wiki_text`, `error_type`, and `error_message` behavior.
- Add focused regressions for missing-ID serialization and source iterator ledger records.

## Type Of Change

- Source-collection ergonomics improvement
- Ledger/audit record improvement
- Test addition/modification

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| `PageSourceResult.page_id` exposes an already-loaded ID and returns `None` when not loaded. | `TestSitePagesAccessor.test_source_result_page_id_does_not_trigger_lookup` constructs a result around a page with `_id = None` and expects `result.page_id is None`. | A change that calls `Page.id`, performs a lookup, raises a missing-ID exception, or needs live Wikidot rejects this local completion claim. |
| Source-result ledger dictionaries include the numeric page ID for successful and failed rows. | `TestSitePagesAccessor.test_iter_sources_result_exports_ledger_record` asserts exact dictionaries containing `"page_id": 371` and `"page_id": 372`. | Missing `page_id`, stringified IDs, raw `Page` objects, raw `PageSource` objects, or raw `Exception` objects reject this local completion claim. |
| Existing source iterator behavior is unchanged. | Focused tests obtain successful and failed rows through `site.pages.iter_sources(...)`; `TestSitePagesAccessor` passed 13 tests; `tests/unit/test_site.py` passed 72 tests. | Regressions in batching, fallback retry, result ordering, parse failure isolation, error typing, or no-login behavior reject this local completion claim. |
| Broad unit and static quality gates remain green. | `uv run pytest tests/unit -q`; `uv run ruff format src tests`; `uv run ruff check src tests`; `uv run ruff format --check src tests`; `uv run mypy src tests`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject this local completion claim. |

## Testing

Implemented locally in commit `14a81f7 feat(site): expose source result page ids`.

- RED: `uv run pytest tests/unit/test_site.py::TestSitePagesAccessor::test_source_result_page_id_does_not_trigger_lookup -q` failed before the fix with `AttributeError: 'PageSourceResult' object has no attribute 'page_id'`.
- GREEN: `uv run pytest tests/unit/test_site.py::TestSitePagesAccessor::test_source_result_page_id_does_not_trigger_lookup -q`.
- RED: `uv run pytest tests/unit/test_site.py::TestSitePagesAccessor::test_iter_sources_result_exports_ledger_record -q` failed before the `as_dict()` update because the returned dictionary omitted `page_id`.
- GREEN: `uv run pytest tests/unit/test_site.py::TestSitePagesAccessor::test_iter_sources_result_exports_ledger_record -q`.
- `uv run pytest tests/unit/test_site.py::TestSitePagesAccessor -q` passed 13 tests.
- `uv run pytest tests/unit/test_site.py -q` passed 72 tests.
- `uv run pytest tests/unit -q` passed 768 tests.
- `uv run ruff format src tests` left 80 files unchanged.
- `uv run ruff check src tests`.
- `uv run ruff format --check src tests`.
- `uv run mypy src tests`.
- `git diff --check`.

Not run successfully: `pyright --version` because this environment could not find a `pyright` executable.

## Acceptance Criteria

- `PageSourceResult.page_id` returns the page ID already present on the wrapped `Page`.
- `PageSourceResult.page_id` returns `None` when the wrapped `Page` has no loaded ID.
- Reading `PageSourceResult.page_id` and `PageSourceResult.as_dict()` does not trigger lazy page-ID acquisition or live network work.
- Successful source iterator result dictionaries include `fullname`, `page_id`, `ok`, `wiki_text`, `error_type`, and `error_message`.
- Failed source iterator result dictionaries include the same keys with `wiki_text: None`, `ok: False`, and the failure type/message.
- Existing source iterator batching, fallback retry, parse failure isolation, result ordering, and source fetch behavior remain unchanged.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, non-goals, verification, and false-positive rejection checks.
- `Issues/README.md` records the local draft and implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

Source-collection workflows commonly write durable per-page ledgers for later retry, comparison, and audit. A numeric page ID gives those rows a stable page identity alongside `fullname`, without requiring callers to reach back into `Page` internals or perform a second lookup while serializing results. Returning `None` for unloaded IDs keeps the helper safe for manually constructed results and avoids surprising network side effects.

## Local Evidence, Not For Upstream Paste

- The broader local large-corpus source collection draft records practical workflows that needed structured source success/failure records and resumable persistence.
- Local follow-ups already added `fullname`, `wiki_text`, `error_message`, `error_type`, and `as_dict()` because source ledgers repeatedly need those values.
- The earlier ledger-record slice intentionally avoided page IDs; this follow-up adds only the already-loaded page ID after publish-result ledgers established `page_id` as useful audit context.
- Keep private rollout paths, corpus identifiers, account names, thread workspace paths, raw command transcripts, raw page source, and sandbox details out of upstream discussion.

## Additional Notes

This slice intentionally does not change source fetching, fallback retry, response parsing, page-ID lookup behavior, JSON encoding helpers, file writing, or live Wikidot behavior. It only exposes page identity that is already available on source iterator result pages and includes it in the existing compact ledger dictionary.
