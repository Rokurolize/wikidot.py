# PR Draft: Include Page Context In Source Iterator Failures

## Summary

Large source-collection scripts need to persist per-page failures without aborting the whole run. `site.pages.iter_sources(...)` already yields a `PageSourceResult` with `page`, `source`, and `error`, but the fallback failure message was generic: `Cannot find page source`.

The fix keeps the same result shape and exception type while adding the page fullname to the failure message, for example `Cannot find page source: page-three`. This makes plain-text failure logs useful even when callers persist `str(result.error)` separately from the page object.

## Related Issue

Drafted from the broader local feature draft in [004-feature-large-corpus-page-source-collection.md](004-feature-large-corpus-page-source-collection.md); no upstream issue filed yet.

## Changes

- Keep unresolved source fetches as `PageSourceResult(ok=False, source=None, error=NotFoundException(...))`.
- Include `page.fullname` in the per-page source failure message.
- Preserve successful source results and search-order result ordering.
- Tighten the existing source fallback test to assert useful per-page error text.

## Type Of Change

- [x] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update
- [ ] Refactoring
- [x] Performance/reliability improvement
- [x] Test addition/modification
- [ ] CI/CD or build related

## Testing

Local implementation commit: `988bbea fix(site): include page name in source failures`

- [x] `uv run --extra test pytest tests/unit/test_site.py::TestSitePagesAccessor::test_iter_sources_falls_back_and_reports_page_failures -q` failed before the fix because `str(result.error)` did not include the failed page fullname and passed after the fix.
- [x] `uv run --extra test pytest tests/unit/test_site.py::TestSitePagesAccessor -q` passed with 5 tests.
- [x] `uv run --extra test pytest tests/unit -q` passed with 552 tests.
- [x] `uv run ruff check .`
- [x] `uv run ruff format --check .`
- [x] `uv run mypy src tests`
- [x] `git diff --check`
- [x] `python3 /home/roku/.codex/skills/complexity-optimizer/scripts/analyze_complexity.py /home/roku/codex-thread-workspaces/019e8a3a-20fd-7113-975d-8c92336695cd/worktrees/wikidot.py --format markdown` inspected current complexity leads.

## Acceptance Criteria

- A permanently unresolved source fetch still yields a failed `PageSourceResult` instead of aborting the iterator.
- The failed result still exposes the original `result.page`.
- `str(result.error)` includes the failed page fullname.
- Existing successful source results, fallback retry calls, result ordering, and batch sizing remain unchanged.
- Existing `site.pages.iter_search(...)`, `site.pages.iter_sources(...)`, and full unit tests continue to pass.

## Upstream-Safe Motivation

Source collection workflows often write compact ledgers of failures for later retry. Including the page fullname in the failure text improves those ledgers without changing the iterator API or adding a new result type.

## Local Evidence, Not For Upstream Paste

- Local rollout evidence recorded source fetch timeout problems during large corpus collection, including repeated timeouts for individual pages.
- Local rollout evidence also included an adapter that emitted per-page failures after fallback source fetch attempts.
- The broader source collection draft in [004-feature-large-corpus-page-source-collection.md](004-feature-large-corpus-page-source-collection.md) calls for structured per-page source failure reporting.

## Additional Notes

This slice does not change retry counts, fallback batch sizing, or the `PageSourceResult` dataclass fields. It only makes the existing failure object more useful when rendered or logged.
