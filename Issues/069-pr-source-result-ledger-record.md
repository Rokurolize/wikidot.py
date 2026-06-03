# PR Draft: Export Source Result Ledger Records

## Summary

Large source-collection callers often persist `site.pages.iter_sources(...)` results as compact ledgers. Previous local slices exposed `PageSourceResult.fullname`, `wiki_text`, and `error_message`, but each caller still had to repeat the same success/failure dictionary construction before writing JSONL, TSV-derived records, or retry ledgers.

This change adds `PageSourceResult.as_dict()`, returning a compact side-effect-free dictionary with `fullname`, `ok`, `wiki_text`, and `error_message`. It reuses existing read-only result properties and does not change source fetching, retry handling, fallback behavior, parsing, cache behavior, or the underlying `PageSourceResult` fields.

## Related Issue

Builds on [004-feature-large-corpus-page-source-collection.md](004-feature-large-corpus-page-source-collection.md), [019-pr-page-source-iterator-fallback.md](019-pr-page-source-iterator-fallback.md), [027-pr-source-result-wiki-text.md](027-pr-source-result-wiki-text.md), and [052-pr-source-result-context-properties.md](052-pr-source-result-context-properties.md). It also complements [051-pr-preserve-source-batch-successes.md](051-pr-preserve-source-batch-successes.md) and [068-pr-preserve-required-tag-search-chunk-size.md](068-pr-preserve-required-tag-search-chunk-size.md), which keep source-collection iteration reliable before result persistence.

No upstream issue was filed from this local workspace.

## Changes

- Add `PageSourceResult.as_dict() -> dict[str, str | bool | None]`.
- Return exactly `fullname`, `ok`, `wiki_text`, and `error_message`.
- Preserve existing `PageSourceResult.page`, `source`, `error`, `ok`, `fullname`, `wiki_text`, and `error_message` behavior.
- Add a focused public-interface regression test that obtains successful and failed results through `site.pages.iter_sources(...)` and serializes both result shapes.

## Type Of Change

- New feature
- Source-collection ergonomics improvement
- Test addition/modification

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| Source result records can be exported without caller-side success/failure branching. | `TestSitePagesAccessor.test_iter_sources_result_exports_ledger_record` asserts `result.as_dict()` for one successful and one failed source result. | The RED test failed before the fix with `AttributeError: 'PageSourceResult' object has no attribute 'as_dict'`. |
| The record shape stays compact and ledger-friendly. | The focused test asserts keys and values for `fullname`, `ok`, `wiki_text`, and `error_message`. | Adding raw `Page`, `PageSource`, or `Exception` objects would fail the exact dictionary assertion and make simple persistence harder. |
| Existing source iterator behavior is unchanged. | The same test obtains records through `site.pages.iter_sources(...)`, and related source result tests still pass. | Any fetching, fallback, ordering, or error-regression would break the focused source iterator tests. |
| Static quality gates remain green. | `tests/unit`; ruff; format; mypy; diff check. | Formatting, lint, type, whitespace, or broad unit failures reject the local completion claim. |

## Testing

Implemented locally in commit `ae4d210 feat(site): export source result ledger records`.

- RED: `uv run --extra test pytest tests/unit/test_site.py::TestSitePagesAccessor::test_iter_sources_result_exports_ledger_record -q` failed before the fix with `AttributeError: 'PageSourceResult' object has no attribute 'as_dict'`.
- GREEN: `uv run --extra test pytest tests/unit/test_site.py::TestSitePagesAccessor::test_iter_sources_result_exports_ledger_record -q`
- `uv run --extra test pytest tests/unit/test_site.py::TestSitePagesAccessor::test_iter_sources_result_exposes_wiki_text tests/unit/test_site.py::TestSitePagesAccessor::test_iter_sources_result_exposes_page_context tests/unit/test_site.py::TestSitePagesAccessor::test_iter_sources_result_exports_ledger_record -q` passed 3 tests.
- `uv run --extra test pytest tests/unit/test_site.py::TestSitePagesAccessor -q` passed 12 tests.
- `uv run --extra test pytest tests/unit/test_site.py -q` passed 52 tests.
- `uv run --extra test pytest tests/unit -q` passed 624 tests.
- `uv run ruff check .`
- `uv run ruff format --check .`
- `uv run mypy src tests`
- `git diff --check`
- `python3 /home/roku/.codex/skills/complexity-optimizer/scripts/analyze_complexity.py /home/roku/codex-thread-workspaces/019e8a3a-20fd-7113-975d-8c92336695cd/worktrees/wikidot.py --format markdown` refreshed current complexity leads.

## Acceptance Criteria

- Successful source iterator results expose `as_dict()` as `{"fullname": ..., "ok": True, "wiki_text": ..., "error_message": None}`.
- Failed source iterator results expose `as_dict()` as `{"fullname": ..., "ok": False, "wiki_text": None, "error_message": ...}`.
- `as_dict()` does not include raw `Page`, `PageSource`, or `Exception` objects.
- Existing `ok`, `fullname`, `wiki_text`, and `error_message` properties remain unchanged.
- Existing source iterator batching, fallback retry, result ordering, parse failure handling, and source fetch behavior remain unchanged.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Source-collection workflows commonly need to write durable per-page ledgers that can be resumed or audited later. A compact `as_dict()` method lets callers persist success and failure rows without repeating optional-source and optional-error branching at every call site, while keeping the richer `PageSourceResult` object available for callers that need page or exception objects.

## Local Evidence, Not For Upstream Paste

- The broader local large-corpus source collection draft records practical workflows that needed structured source success/failure records and resumable persistence.
- Local follow-ups already added `wiki_text`, `fullname`, and `error_message` because source ledgers repeatedly need those values.
- Keep private rollout paths, corpus identifiers, account names, thread workspace paths, raw command transcripts, and sandbox details out of upstream discussion.

## Additional Notes

This slice intentionally avoids adding page IDs, raw object serialization, JSON encoding helpers, or file writing. It only exports the existing ledger-friendly fields from `PageSourceResult`.
