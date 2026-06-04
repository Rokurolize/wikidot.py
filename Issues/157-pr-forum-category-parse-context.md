# PR Draft: Include Site Context In Forum Category Parse Errors

## Summary

`ForumCategoryCollection.acquire_all(...)`, used by `site.forum.categories`, parses forum category rows returned by `forum/ForumStartModule`. The parser already fails when generated category markup is malformed, but the remaining category row, field, link, and description failures only named the missing element. A plain log line such as `Category row is malformed.` did not identify which site or which structural category row produced the malformed shape.

This follow-up keeps the existing `NoElementException` failure behavior and category output shape, but includes the affected site `unix_name`, structural row index, and observed direct cell count where relevant. That makes forum category parser failures diagnosable from plain-text logs without saving raw forum-start HTML or category descriptions.

## Related Issue

Builds on [033-pr-retry-forum-category-list-fetches.md](033-pr-retry-forum-category-list-fetches.md), [086-pr-ignore-nested-category-tables.md](086-pr-ignore-nested-category-tables.md), [108-pr-preserve-forum-category-description-spacing.md](108-pr-preserve-forum-category-description-spacing.md), and [111-pr-preserve-forum-category-title-spacing.md](111-pr-preserve-forum-category-title-spacing.md).

No upstream issue was filed from this local workspace.

## Changes

- Add a small forum-category parse-context helper for site name, structural category row index, and optional observed counts.
- Include that context in malformed category row, missing name/thread-count/post-count cell, missing title/link/href/category-id, and missing description `NoElementException` messages.
- Add a focused malformed category-row regression that asserts `Category row is malformed for site: test-site (row=1, cells=2)`.
- Preserve retry-aware category fetching, empty forum indexes, nested category-table filtering, title/description text spacing, category field parsing, category thread access, and thread creation behavior.

## Type Of Change

- Bug fix / diagnostics improvement
- Forum category parser error-context ergonomics
- Test addition

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| Malformed forum category rows still fail. | `TestForumCategoryCollectionAcquireAll.test_acquire_all_malformed_row_includes_site_context` still expects `NoElementException` for a structural category row with only two direct cells. | A change that silently accepts the malformed row, fabricates counts, or shifts parser output rejects this local completion claim. |
| The malformed row error identifies the affected site, structural row, and observed cell count. | The focused test asserts `Category row is malformed for site: test-site (row=1, cells=2)`. | The RED test failed before the fix because the exception message was only `Category row is malformed.` |
| Related category parser failures use the same site/row context helper. | Source inspection of `src/wikidot/module/forum_category.py` shows row, cell-class, title/link/href/category-id, and description `NoElementException` messages all append the parse context. | A future partial context change that only updates malformed-row errors would leave the other category parser failures as generic log lines. |
| Forum category workflows remain green. | `uv run --extra test pytest tests/unit/test_forum_category.py -q` passed 19 tests. | Regressions in normal parsing, title/description spacing, nested category-table filtering, empty indexes, retry exhaustion, or thread creation reject this local completion claim. |
| Adjacent forum workflows remain green. | `uv run --extra test pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed 144 tests. | Regressions in category, thread, post, or post-revision behavior reject this local completion claim. |
| Broad unit and static quality gates remain green. | `uv run pytest tests/unit -q`; `uv run ruff check`; `uv run ruff format --check`; `uv run mypy src tests --install-types --non-interactive`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject this local completion claim. |

## Testing

Implemented locally in commit `5ae5d55 fix(forum_category): include context in parse errors`.

- RED: `uv run --extra test pytest tests/unit/test_forum_category.py::TestForumCategoryCollectionAcquireAll::test_acquire_all_malformed_row_includes_site_context -q` failed before the fix because the parser raised `Category row is malformed.` without site, row index, or observed cell count.
- GREEN: `uv run --extra test pytest tests/unit/test_forum_category.py::TestForumCategoryCollectionAcquireAll::test_acquire_all_malformed_row_includes_site_context -q`
- `uv run --extra test pytest tests/unit/test_forum_category.py -q` passed 19 tests.
- `uv run --extra test pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed 144 tests.
- `uv run pytest tests/unit -q` passed 716 tests.
- `uv run ruff check`
- `uv run ruff format --check`
- `uv run mypy src tests --install-types --non-interactive`
- `git diff --check`

Not run successfully: `uv run pyright` because this environment could not find a `pyright` executable.

## Acceptance Criteria

- A forum category response whose structural category row has too few direct cells still raises `NoElementException`.
- The raised malformed-row message includes the site `unix_name`, structural row index, and observed direct cell count.
- Other malformed category row field failures also include the same site/row context.
- Successful category parsing, nested category-table filtering, retry behavior, empty forum indexes, title and description text spacing, category thread access, and thread creation action payloads remain unchanged.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Forum category inspection is a read-heavy prerequisite for thread, post, and revision collection. When Wikidot returns malformed generated forum-start markup, wikidot.py should still fail instead of inventing categories, but the failure should identify the affected site and structural row so maintainers can triage without storing raw forum-start HTML or rendered category descriptions.

## Local Evidence, Not For Upstream Paste

- Earlier local drafts established forum categories as a practical read-heavy workflow, including retry-aware category-list fetches, structural parser boundaries, nested category-table filtering, and title/description text spacing.
- Recent parser and direct-property context work showed that target-specific errors improve plain-text logs and resumable ledgers without changing successful behavior.
- The refreshed complexity memo continues to list `src/wikidot/module/forum_category.py` as an audit-worthy parser/acquisition surface.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, raw forum-start HTML, and category contents out of upstream discussion.

## Additional Notes

This slice intentionally does not change `ForumCategoryCollection.acquire_all(...)` request construction, retry handling, empty result handling, successful parser output, nested category-table filtering, title/description extraction, category field values, `ForumCategory.threads`, `ForumCategory.reload_threads()`, `ForumCategory.create_thread(...)`, or live Wikidot behavior. It only adds site and structural-row context to existing malformed forum category parse failures.
