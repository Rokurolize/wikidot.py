# PR Draft: Expose Publish Aggregate Status Properties

## Summary

Browser-free publishing callers often write audit rows after `site.page.publish(...)`. The helper already returns individual operation fields such as `source_matches`, `tags_updated`, `parent_updated`, and `metas_updated`, but callers still have to repeat small boolean expressions to answer two common questions: did any metadata operation run, and did source verification finish with a match?

The fix adds read-only `PagePublishResult.metadata_updated` and `PagePublishResult.source_verified` properties. They preserve all existing result fields and publish behavior while making audit code easier to read.

## Related Issue

Drafted from the broader local feature draft in [003-feature-browser-free-page-publisher.md](003-feature-browser-free-page-publisher.md); no upstream issue filed yet.

## Changes

- Add `PagePublishResult.metadata_updated`, true when tags, parent, or meta tags were updated by the publish call.
- Add `PagePublishResult.source_verified`, true when source verification was requested and matched.
- Preserve `source_matches`, `tags_updated`, `parent_updated`, `metas_updated`, `created`, and publish sequencing.
- Add a focused unit test covering verified, skipped, and failed direct result states.

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

Local implementation commit: `d8226d5 feat(site): expose publish aggregate status`

- [x] `uv run --extra test pytest tests/unit/test_site.py::TestSitePageAccessor::test_publish_result_exposes_aggregate_operation_statuses -q` failed before the fix with missing `PagePublishResult.metadata_updated` and passed after the fix.
- [x] `uv run --extra test pytest tests/unit/test_site.py::TestSitePageAccessor -q` passed with 12 tests.
- [x] `uv run --extra test pytest tests/unit -q` passed with 555 tests.
- [x] `uv run ruff check .`
- [x] `uv run ruff format --check .`
- [x] `uv run mypy src tests`
- [x] `git diff --check`
- [x] `python3 /home/roku/.codex/skills/complexity-optimizer/scripts/analyze_complexity.py /home/roku/codex-thread-workspaces/019e8a3a-20fd-7113-975d-8c92336695cd/worktrees/wikidot.py --format markdown` inspected current complexity leads.

## Acceptance Criteria

- Results with any tags, parent, or meta update expose `result.metadata_updated is True`.
- Results without metadata updates expose `result.metadata_updated is False`.
- Results with `source_matches is True` expose `result.source_verified is True`.
- Results with skipped or failed source verification expose `result.source_verified is False`.
- Existing publish create/edit, metadata, source verification, normalization, visibility retry, and result fields continue to behave unchanged.

## Upstream-Safe Motivation

Structured publish result data is most useful when callers can persist concise audit fields without duplicating helper internals. Aggregate status properties make the high-level publish helper easier to use in scripts while keeping the lower-level booleans available for detailed decisions.

## Local Evidence, Not For Upstream Paste

- The broader local feature draft in [003-feature-browser-free-page-publisher.md](003-feature-browser-free-page-publisher.md) calls for structured result data with source verification status and metadata operation statuses.
- Local browser-free publishing rollout evidence included scripts that wrote ledgers after saving, verifying source, and updating tags, parent, or meta tags.
- Earlier local drafts [017-pr-browser-free-page-publish-helper.md](017-pr-browser-free-page-publish-helper.md), [020-pr-publish-source-verification-normalizer.md](020-pr-publish-source-verification-normalizer.md), [021-pr-publish-post-save-visibility-retry.md](021-pr-publish-post-save-visibility-retry.md), and [024-pr-publish-create-outcome.md](024-pr-publish-create-outcome.md) added the base helper and publish-result status fields this convenience layer builds on.

## Additional Notes

This slice does not add partial-failure result objects. Failed publish operations still raise the existing wikidot.py exceptions instead of returning a partial success record.
