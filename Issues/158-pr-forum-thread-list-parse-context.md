# PR Draft: Include Category Context In Forum Thread List Parse Errors

## Summary

`ForumThreadCollection.acquire_all_in_category(...)`, used by `ForumCategory.threads`, parses category thread-list rows returned by `forum/ForumViewCategoryModule`. The parser already fails when generated thread-list markup has the wrong structural cell classes or missing required elements, but those failures only named the missing element. A plain log line such as `Thread name element is not found.` did not identify which site, category, page, or structural row produced the malformed shape.

This follow-up keeps the existing `NoElementException` failure behavior and thread output shape, but includes the affected site `unix_name`, category ID, category page, structural row index, and observed direct cell count where relevant. That makes category thread-list parser failures diagnosable from plain-text logs without saving raw forum HTML or thread descriptions.

## Related Issue

Builds on [034-pr-retry-category-thread-list-fetches.md](034-pr-retry-category-thread-list-fetches.md), [084-pr-scope-thread-list-metadata.md](084-pr-scope-thread-list-metadata.md), [087-pr-ignore-nested-thread-tables.md](087-pr-ignore-nested-thread-tables.md), [098-pr-ignore-thread-description-pager-markup.md](098-pr-ignore-thread-description-pager-markup.md), [107-pr-preserve-thread-list-description-spacing.md](107-pr-preserve-thread-list-description-spacing.md), [110-pr-preserve-thread-list-title-spacing.md](110-pr-preserve-thread-list-title-spacing.md), and [136-pr-skip-cached-category-thread-list-fetches.md](136-pr-skip-cached-category-thread-list-fetches.md).

This is the thread-list companion to [157-pr-forum-category-parse-context.md](157-pr-forum-category-parse-context.md), which added site/row context to forum category parser failures.

No upstream issue was filed from this local workspace.

## Changes

- Add a small category thread-list parse-context helper for site name, category ID, category page, structural row index, and optional observed counts.
- Pass the current category page into `ForumThreadCollection._parse_list_in_category(...)` from first-page and paginated acquisitions.
- Include the context in missing name/started/posts cell, title, title href, thread ID, description, user, and odate `NoElementException` messages.
- Add a focused malformed thread-list cell regression that asserts `Thread name element is not found for site: test-site (category=1001, page=1, row=1, cells=4)`.
- Preserve retry-aware category thread-list fetching, cached category thread reuse, explicit reload behavior, pagination, nested thread-table filtering, description-pager filtering, title/description spacing, direct thread lookup, post access, and replies.

## Type Of Change

- Bug fix / diagnostics improvement
- Forum thread-list parser error-context ergonomics
- Test addition

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| Malformed category thread-list rows still fail when a required structural cell class is missing. | `TestForumThreadCollectionAcquireAll.test_acquire_all_missing_name_cell_class_includes_category_context` still expects `NoElementException` when the first structural row has `td.wrong` instead of `td.name`. | A change that silently accepts the malformed row, fabricates thread data, or shifts parser output rejects this local completion claim. |
| The malformed row error identifies the affected site, category, page, structural row, and observed cell count. | The focused test asserts `Thread name element is not found for site: test-site (category=1001, page=1, row=1, cells=4)`. | The RED test failed before the fix because the exception message was only `Thread name element is not found.` |
| Related thread-list parser failures use the same context helper. | Source inspection of `src/wikidot/module/forum_thread.py` shows cell-class, title, title-href, thread-ID, description, user, and odate `NoElementException` messages all append the parse context. | A future partial context change that only updates the name-cell failure would leave the other thread-list parser failures as generic log lines. |
| Forum thread-list workflows remain green. | `uv run --extra test pytest tests/unit/test_forum_thread.py -q` passed 41 tests. | Regressions in normal parsing, cached category reuse, reloads, pagination, retry exhaustion, nested thread-table filtering, description-pager filtering, title/description spacing, direct thread lookup, post access, or replies reject this local completion claim. |
| Adjacent forum workflows remain green. | `uv run --extra test pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed 145 tests. | Regressions in category, thread, post, or post-revision behavior reject this local completion claim. |
| Broad unit and static quality gates remain green. | `uv run pytest tests/unit -q`; `uv run ruff check`; `uv run ruff format --check`; `uv run mypy src tests --install-types --non-interactive`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject this local completion claim. |

## Testing

Implemented locally in commit `c633c85 fix(forum_thread): include context in list parse errors`.

- RED: `uv run --extra test pytest tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireAll::test_acquire_all_missing_name_cell_class_includes_category_context -q` failed before the fix because the parser raised `Thread name element is not found.` without site, category, page, row index, or observed cell count.
- GREEN: `uv run --extra test pytest tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireAll::test_acquire_all_missing_name_cell_class_includes_category_context -q`
- `uv run --extra test pytest tests/unit/test_forum_thread.py -q` passed 41 tests.
- `uv run --extra test pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed 145 tests.
- `uv run pytest tests/unit -q` passed 717 tests.
- `uv run ruff check`
- `uv run ruff format --check`
- `uv run mypy src tests --install-types --non-interactive`
- `git diff --check`

Not run successfully: `uv run pyright` because this environment could not find a `pyright` executable.

## Acceptance Criteria

- A category thread-list response whose structural thread row has an invalid required cell class still raises `NoElementException`.
- The raised malformed-cell message includes the site `unix_name`, category ID, category page, structural row index, and observed direct cell count.
- Other malformed thread-list field failures also include the same category/page/row context.
- Successful thread-list parsing, cached category thread reuse, reloads, pagination, nested thread-table filtering, description-pager filtering, title and description text spacing, direct thread lookup, post access, and reply action payloads remain unchanged.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Category thread-list inspection is a read-heavy prerequisite for discussion, post, and revision collection. When Wikidot returns malformed generated category thread-list markup, wikidot.py should still fail instead of inventing threads, but the failure should identify the affected site, category, page, and structural row so maintainers can triage without storing raw forum HTML or rendered thread descriptions.

## Local Evidence, Not For Upstream Paste

- Earlier local drafts established category thread-list acquisition as a practical read-heavy workflow, including retry-aware category thread-list fetches, structural parser boundaries, nested thread-table filtering, description-pager filtering, title/description text spacing, and cached category thread-list reuse.
- The previous forum category parse-context slice showed that target-specific parser errors improve plain-text logs and resumable ledgers without changing successful behavior.
- The refreshed complexity memo continues to list `src/wikidot/module/forum_thread.py` as an audit-worthy parser/acquisition surface.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, raw forum HTML, and thread contents out of upstream discussion.

## Additional Notes

This slice intentionally does not change `ForumThreadCollection.acquire_all_in_category(...)` request construction, retry handling, cache semantics, reload semantics, pagination, successful parser output, nested thread-table filtering, description-pager filtering, title/description extraction, thread field values, direct thread lookup, `ForumThread.posts`, `ForumThread.reply(...)`, or live Wikidot behavior. It only adds site, category, page, row, and observed-count context to existing malformed category thread-list parse failures.
