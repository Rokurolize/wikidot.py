# PR Draft: Expose Wiki Text On Source Iterator Results

## Summary

Large source-collection callers usually want the page fullname, the raw Wikidot source text, and any per-page error. `site.pages.iter_sources(...)` already yields `PageSourceResult` records with `page`, `source`, `error`, and `ok`, but callers still have to write the same optional-source guard before reading the text:

```python
wiki_text = result.source.wiki_text if result.source is not None else None
```

The fix adds a read-only `PageSourceResult.wiki_text` property. Successful results return `result.source.wiki_text`; failed results return `None`. The existing `source`, `error`, and `ok` behavior remains unchanged.

## Related Issue

Drafted from the broader local feature draft in [004-feature-large-corpus-page-source-collection.md](004-feature-large-corpus-page-source-collection.md); no upstream issue filed yet.

## Changes

- Add `PageSourceResult.wiki_text -> str | None`.
- Return the underlying `PageSource.wiki_text` when source retrieval succeeded.
- Return `None` when source retrieval failed or no `PageSource` is present.
- Preserve `PageSourceResult.source`, `PageSourceResult.error`, and `PageSourceResult.ok`.
- Add a focused iterator test covering successful and failed source results.

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

Local implementation commit: `68b7d8f feat(site): expose source result wiki text`

- [x] `uv run --extra test pytest tests/unit/test_site.py::TestSitePagesAccessor::test_iter_sources_result_exposes_wiki_text -q` failed before the fix with missing `PageSourceResult.wiki_text` and passed after the fix.
- [x] `uv run --extra test pytest tests/unit/test_site.py::TestSitePagesAccessor -q` passed with 7 tests.
- [x] `uv run --extra test pytest tests/unit -q` passed with 554 tests.
- [x] `uv run ruff check .`
- [x] `uv run ruff format --check .`
- [x] `uv run mypy src tests`
- [x] `git diff --check`
- [x] `python3 /home/roku/.codex/skills/complexity-optimizer/scripts/analyze_complexity.py /home/roku/codex-thread-workspaces/019e8a3a-20fd-7113-975d-8c92336695cd/worktrees/wikidot.py --format markdown` inspected current complexity leads.

## Acceptance Criteria

- Successful source iterator results expose `result.wiki_text` equal to `result.source.wiki_text`.
- Failed source iterator results expose `result.wiki_text is None`.
- Existing `result.source`, `result.error`, and `result.ok` behavior remains unchanged.
- Existing source iterator batching, fallback retry, ordering, and per-page failure behavior remains unchanged.
- Existing `site.pages.iter_sources(...)` and full unit tests continue to pass.

## Upstream-Safe Motivation

Most source collection scripts are interested in the source text itself, not just the wrapper object. A direct `wiki_text` property makes the structured result easier to persist and reduces repeated optional-source boilerplate while keeping the current API shape intact.

## Local Evidence, Not For Upstream Paste

- Local rollout evidence recorded large corpus and dependency workflows that needed to persist exact Wikidot source text for many pages.
- Local rollout evidence included an anonymous source fetcher that generated exact `wikidot_view_source` files for public dependency pages.
- The broader source collection draft in [004-feature-large-corpus-page-source-collection.md](004-feature-large-corpus-page-source-collection.md) centers on structured source success/failure records for resumable collection.

## Additional Notes

This slice does not change source fetching, retry behavior, parsing, fallback batch sizing, or the `PageSource` object. It only adds a convenience property to the result record returned by `site.pages.iter_sources(...)`.

Follow-up [052-pr-source-result-context-properties.md](052-pr-source-result-context-properties.md) exposes the same result record's page fullname and error message directly for compact source-collection ledgers.
