# PR Draft: Add Publish Source Verification Normalizer

## Summary

Browser-free publishing callers sometimes need to compare saved Wikidot source after applying a known normalization policy. The default exact comparison is still the safest library default, but `site.page.publish(...)` now accepts an optional `source_normalizer` callable that is applied to both submitted and fetched source before verification.

This keeps the common publish helper useful for rollout-style scripts that normalize harmless source differences while preserving strict verification behavior for callers that do not opt in.

## Related Issue

Drafted from the broader local feature draft in [003-feature-browser-free-page-publisher.md](003-feature-browser-free-page-publisher.md); no upstream issue filed yet.

## Changes

- Add `source_normalizer: Callable[[str], str] | None = None` to `site.page.publish(...)`.
- Preserve exact source comparison when `source_normalizer` is omitted.
- When `verify_source=True` and a normalizer is provided, apply it to both `Page.refresh_source().wiki_text` and the submitted `source` before comparing.
- Preserve the existing `UnexpectedException` failure path when normalized source still mismatches.
- Add a unit test covering caller-supplied normalization of fetched and submitted source.

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

Local implementation commit: `ebb3434 feat(site): normalize publish source verification`

- [x] `uv run --extra test pytest tests/unit/test_site.py::TestSitePageAccessor::test_publish_verifies_source_with_custom_normalizer -q` failed before the fix with unexpected keyword argument `source_normalizer` and passed after the fix.
- [x] `uv run --extra test pytest tests/unit/test_site.py::TestSitePageAccessor -q` passed with 9 tests.
- [x] `uv run --extra test pytest tests/unit -q` passed with 547 tests.
- [x] `uv run ruff check .`
- [x] `uv run ruff format --check .`
- [x] `uv run mypy src tests`
- [x] `git diff --check`
- [x] `python3 /home/roku/.codex/skills/complexity-optimizer/scripts/analyze_complexity.py /home/roku/codex-thread-workspaces/019e8a3a-20fd-7113-975d-8c92336695cd/worktrees/wikidot.py --format markdown` inspected current complexity leads.

## Acceptance Criteria

- `site.page.publish(..., verify_source=True)` keeps exact source comparison by default.
- Callers can provide `source_normalizer` without changing create/edit or metadata behavior.
- The normalizer is applied symmetrically to fetched source and submitted source.
- Normalized matches return `PagePublishResult.source_matches is True`.
- Normalized mismatches still raise `UnexpectedException`.
- Existing publish tests for create, edit, metadata update, and strict mismatch behavior continue to pass.

## Upstream-Safe Motivation

Wikidot source round-trip checks can be useful even when callers need a project-specific normalization rule for whitespace or include formatting. Letting callers inject that rule avoids baking one policy into wikidot.py while still keeping verification in the library-tested publish workflow.

## Local Evidence, Not For Upstream Paste

- Local rollout `019e7a39-505b-76b3-bfb4-b68be3c71fb9` included a publishing script that normalized submitted and fetched source before round-trip comparison.
- The broader local feature draft in [003-feature-browser-free-page-publisher.md](003-feature-browser-free-page-publisher.md) explicitly kept custom source normalization hooks as a follow-up design choice after the first publish helper slice.
- The first publish helper draft in [017-pr-browser-free-page-publish-helper.md](017-pr-browser-free-page-publish-helper.md) noted that custom source normalization was intentionally left for a later slice.

## Additional Notes

This slice does not add an opinionated built-in normalizer. The post-save visibility follow-up is drafted in [021-pr-publish-post-save-visibility-retry.md](021-pr-publish-post-save-visibility-retry.md). Callers remain responsible for choosing a normalization policy appropriate for their content.
