# PR Draft: Expose Source Result Context Properties

## Summary

Large source-collection callers often persist compact ledgers with a page fullname, source text, and failure message. `site.pages.iter_sources(...)` already yields `PageSourceResult` records with `page`, `source`, `error`, `ok`, and `wiki_text`, but callers still have to repeat `result.page.fullname` and `str(result.error) if result.error is not None else None` in every ledger writer.

The fix adds read-only `PageSourceResult.fullname` and `PageSourceResult.error_message` properties. Successful results expose the page fullname and `error_message is None`; failed results expose the same page fullname and the string form of the existing error. Fetching, retry, fallback, parsing, and the existing result fields remain unchanged.

## Related Issue

Complements the large-corpus source collection draft [004-feature-large-corpus-page-source-collection.md](004-feature-large-corpus-page-source-collection.md), especially the structured source result work in [019-pr-page-source-iterator-fallback.md](019-pr-page-source-iterator-fallback.md), [025-pr-source-result-error-page-context.md](025-pr-source-result-error-page-context.md), [027-pr-source-result-wiki-text.md](027-pr-source-result-wiki-text.md), [049-pr-filter-iterators-by-required-tags.md](049-pr-filter-iterators-by-required-tags.md), and [051-pr-preserve-source-batch-successes.md](051-pr-preserve-source-batch-successes.md). No upstream issue filed yet.

## Changes

- Add `PageSourceResult.fullname -> str`, returning `result.page.fullname`.
- Add `PageSourceResult.error_message -> str | None`, returning `str(result.error)` for failures and `None` for successes.
- Preserve `PageSourceResult.page`, `source`, `error`, `ok`, and `wiki_text`.
- Add a focused iterator test covering successful and failed source result context fields.

## Type Of Change

- [ ] Bug fix
- [x] New feature
- [ ] Breaking change
- [ ] Documentation update
- [ ] Refactoring
- [ ] Performance/reliability improvement
- [x] Test addition/modification
- [ ] CI/CD or build related

## Testing

Local implementation commit: `f92d473 feat(site): expose source result page context`

- [x] `uv run --extra test pytest tests/unit/test_site.py::TestSitePagesAccessor::test_iter_sources_result_exposes_page_context -q` failed before the fix with missing `PageSourceResult.fullname`, then passed after the fix.
- [x] `uv run --extra test pytest tests/unit/test_site.py -q` passed with 50 tests.
- [x] `uv run --extra test pytest tests/unit -q` passed with 607 tests.
- [x] `uv run ruff check .`
- [x] `uv run ruff format --check .`
- [x] `uv run mypy src tests`
- [x] `git diff --check`
- [x] `python3 /home/roku/.codex/skills/complexity-optimizer/scripts/analyze_complexity.py /home/roku/codex-thread-workspaces/019e8a3a-20fd-7113-975d-8c92336695cd/worktrees/wikidot.py --format markdown` refreshed current complexity leads.

## Acceptance Criteria

- Successful source iterator results expose `result.fullname` equal to `result.page.fullname`.
- Failed source iterator results expose `result.fullname` equal to the failed page fullname.
- Successful source iterator results expose `result.error_message is None`.
- Failed source iterator results expose `result.error_message == str(result.error)`.
- Existing source iterator batching, fallback retry, source parsing, result ordering, and existing result fields remain unchanged.
- Existing `site.pages.iter_sources(...)` and full unit tests continue to pass.

## Upstream-Safe Motivation

Source collection workflows need ledger-friendly result records. Direct `fullname` and `error_message` properties reduce repeated boilerplate in callers without changing the iterator protocol or hiding the underlying page and exception objects.

## Local Evidence, Not For Upstream Paste

- Local rollout evidence recorded large corpus and dependency workflows that needed to persist exact source text and per-page failures.
- Existing local source iterator drafts already show callers writing `result.page.fullname`, `result.wiki_text`, and `result.error` into source-collection ledgers.
- The broader source collection draft centers on structured success/failure records for resumable collection.

## Additional Notes

This slice does not change source fetching, retry behavior, fallback batch sizing, parse failure handling, or the `PageSource` object. It only adds read-only convenience properties to the existing `PageSourceResult` record.

Follow-up [069-pr-source-result-ledger-record.md](069-pr-source-result-ledger-record.md) wraps `fullname`, `ok`, `wiki_text`, and `error_message` into a compact `PageSourceResult.as_dict()` ledger record while preserving these individual read-only properties.
