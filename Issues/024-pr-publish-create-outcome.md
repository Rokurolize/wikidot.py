# PR Draft: Report Publish Create/Edit Outcome

## Summary

Browser-free publishing scripts often need audit data that says whether a publish call created a new page or edited an existing page. `site.page.publish(...)` already returns page ID, source verification, and metadata flags, but it did not expose the create/edit branch taken by the helper.

The fix adds `PagePublishResult.created`, which is `True` when `publish(...)` creates a missing page and `False` when it edits an existing page. The field has a default of `False` so direct `PagePublishResult(...)` construction remains compatible.

## Related Issue

Drafted from the broader local feature draft in [003-feature-browser-free-page-publisher.md](003-feature-browser-free-page-publisher.md); no upstream issue filed yet.

## Changes

- Add `created: bool = False` to `PagePublishResult`.
- Set `created=True` in the missing-page create branch of `site.page.publish(...)`.
- Set `created=False` in the existing-page edit branch.
- Add a focused unit test covering both result outcomes.

## Type Of Change

- [ ] Bug fix
- [x] New feature
- [ ] Breaking change
- [ ] Documentation update
- [ ] Refactoring
- [x] Performance/reliability improvement
- [x] Test addition/modification
- [ ] CI/CD or build related

## Testing

Local implementation commit: `763c270 feat(site): report publish create outcome`

- [x] `uv run --extra test pytest tests/unit/test_site.py::TestSitePageAccessor::test_publish_result_reports_create_or_edit_outcome -q` failed before the fix with missing `PagePublishResult.created` and passed after the fix.
- [x] `uv run --extra test pytest tests/unit/test_site.py::TestSitePageAccessor -q` passed with 11 tests.
- [x] `uv run --extra test pytest tests/unit -q` passed with 552 tests.
- [x] `uv run ruff check .`
- [x] `uv run ruff format --check .`
- [x] `uv run mypy src tests`
- [x] `git diff --check`
- [x] `python3 /home/roku/.codex/skills/complexity-optimizer/scripts/analyze_complexity.py /home/roku/codex-thread-workspaces/019e8a3a-20fd-7113-975d-8c92336695cd/worktrees/wikidot.py --format markdown` inspected current complexity leads.

## Acceptance Criteria

- Publishing an existing page returns `PagePublishResult.created is False`.
- Publishing a missing page returns `PagePublishResult.created is True`.
- Existing `PagePublishResult` fields keep their behavior.
- Direct `PagePublishResult(...)` construction without the new field remains valid because the field has a default.
- Existing publish create, edit, source verification, source normalization, post-save visibility, and metadata tests continue to pass.

## Upstream-Safe Motivation

High-level browser-free publishing should return enough structured data for callers to write an audit ledger without reimplementing the helper's page lookup branch. A simple create/edit outcome flag makes publish results easier to inspect while preserving the existing create/edit workflow.

## Local Evidence, Not For Upstream Paste

- The broader local feature draft in [003-feature-browser-free-page-publisher.md](003-feature-browser-free-page-publisher.md) calls for structured publish result data and clear operation status.
- Local browser-free publishing rollout evidence included scripts that manually coordinated save, page ID discovery, source verification, and metadata operations; those scripts needed ledger-friendly result data.
- Earlier local drafts [017-pr-browser-free-page-publish-helper.md](017-pr-browser-free-page-publish-helper.md), [020-pr-publish-source-verification-normalizer.md](020-pr-publish-source-verification-normalizer.md), and [021-pr-publish-post-save-visibility-retry.md](021-pr-publish-post-save-visibility-retry.md) added the base helper and verification/visibility follow-ups.

## Additional Notes

This slice does not add write retries or per-metadata-operation error objects. Failed operations still raise the existing wikidot.py exceptions instead of returning a partial success result.
