# PR Draft: Retry Publish Post-Save Visibility

## Summary

Browser-free publishing can receive a successful `savePage` response before the public page ID is visible through the direct page URL. `site.page.publish(...)` now lets callers opt into bounded post-save visibility polling before metadata updates, source verification, and result return.

The default remains one immediate page ID resolution attempt, preserving the existing no-wait behavior. Callers that know their workflow is sensitive to Wikidot eventual consistency can pass a larger `post_save_visibility_attempts` value and a polling interval.

## Related Issue

Drafted from the broader local feature draft in [003-feature-browser-free-page-publisher.md](003-feature-browser-free-page-publisher.md); no upstream issue filed yet.

## Changes

- Add `post_save_visibility_attempts: int = 1` to `site.page.publish(...)`.
- Add `post_save_visibility_interval: float = 2.0` to `site.page.publish(...)`.
- Resolve the saved page ID before optional metadata updates, optional source verification, and the returned `PagePublishResult`.
- Retry transient direct page ID failures when callers request multiple post-save visibility attempts.
- Retry missing-ID `UnexpectedException`, `NotFoundException`, and direct `404` HTTP status failures, while preserving non-404 HTTP failures.
- Validate that attempts are at least one and interval is non-negative before any save side effects.
- Add a unit test for a newly saved page whose ID becomes visible on a later attempt.

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

Local implementation commit: `bfe364c feat(site): retry publish page visibility`

- [x] `uv run --extra test pytest tests/unit/test_site.py::TestSitePageAccessor::test_publish_retries_post_save_visibility_before_returning_page_id -q` failed before the fix with unexpected keyword argument `post_save_visibility_attempts` and passed after the fix.
- [x] `uv run --extra test pytest tests/unit/test_site.py::TestSitePageAccessor -q` passed with 10 tests.
- [x] `uv run --extra test pytest tests/unit -q` passed with 548 tests.
- [x] `uv run ruff check .`
- [x] `uv run ruff format --check .`
- [x] `uv run mypy src tests`
- [x] `git diff --check`
- [x] `python3 /home/roku/.codex/skills/complexity-optimizer/scripts/analyze_complexity.py /home/roku/codex-thread-workspaces/019e8a3a-20fd-7113-975d-8c92336695cd/worktrees/wikidot.py --format markdown` inspected current complexity leads.

## Acceptance Criteria

- `site.page.publish(...)` keeps one immediate page ID resolution attempt by default.
- Callers can request multiple post-save visibility attempts.
- The helper waits between failed attempts only when the configured interval is positive.
- Transient missing direct page IDs can recover before metadata updates, source verification, and result return.
- Non-404 HTTP errors still propagate without being treated as visibility lag.
- Invalid visibility attempt or interval options are rejected before login and save operations.
- Existing publish create, edit, metadata, strict verification, and source-normalizer behaviors continue to pass.

## Upstream-Safe Motivation

Wikidot can be eventually consistent after a successful page save. A high-level browser-free publish helper should let callers choose a bounded direct visibility wait rather than forcing every automation script to reimplement a page ID polling loop.

## Local Evidence, Not For Upstream Paste

- Local rollout `019e7a39-505b-76b3-bfb4-b68be3c71fb9` included a publishing script that retried direct page ID discovery after `savePage` before fetching source and metadata.
- The integration test in `tests/integration/test_page_lifecycle.py` documents that `ListPagesModule` can briefly return stale metadata after edits, while source and rendered HTML become reliable after waiting.
- The broader local feature draft in [003-feature-browser-free-page-publisher.md](003-feature-browser-free-page-publisher.md) explicitly listed direct page visibility retry after save as part of the desired browser-free workflow.

## Additional Notes

This slice does not retry the `savePage` write itself. Blind write retries can duplicate side effects, so this change retries only post-save page ID visibility.
