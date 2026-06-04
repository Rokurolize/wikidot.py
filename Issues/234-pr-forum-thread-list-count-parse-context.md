# PR Draft: Include Context In Forum Thread List Count Parse Errors

## Summary

`ForumThreadCollection.acquire_all_in_category(...)`, used by `category.threads`, parses thread rows returned by `forum/ForumViewCategoryModule`. The thread-list parser already includes site, category, page, row, and observed cell-count context for malformed row shapes, but malformed post-count text still reached raw `int(...)` conversion and raised a bare `ValueError`.

This follow-up keeps successful parsing and existing `NoElementException` behavior for malformed Wikidot-generated thread-list markup, but routes malformed thread-list post-count values through the same contextual parser-error surface. The raised message now identifies the site, category, page, structural row, affected field, and raw value, so plain-text logs can explain which category thread-list row failed without preserving raw HTML.

## Related Issue

Builds on [034-pr-retry-category-thread-list-fetches.md](034-pr-retry-category-thread-list-fetches.md), [087-pr-ignore-nested-thread-tables.md](087-pr-ignore-nested-thread-tables.md), [107-pr-preserve-thread-list-description-spacing.md](107-pr-preserve-thread-list-description-spacing.md), [110-pr-preserve-thread-list-title-spacing.md](110-pr-preserve-thread-list-title-spacing.md), [158-pr-forum-thread-list-parse-context.md](158-pr-forum-thread-list-parse-context.md), [214-pr-forum-thread-response-body-context.md](214-pr-forum-thread-response-body-context.md), and [233-pr-forum-category-count-parse-context.md](233-pr-forum-category-count-parse-context.md). Those drafts established retry-aware category thread-list acquisition, structural parser boundaries, title/description preservation, row-level parse context, response-body validation, and the adjacent count-value parser diagnostic pattern.

No upstream issue was filed from this local workspace.

## Changes

- Add a small thread-list count parser that converts post-count cell text to `int` and raises `NoElementException` on malformed values.
- Include site, category, page, structural row index, field, and raw count value in malformed thread-list post-count errors.
- Extend category thread-list acquisition tests to cover a malformed post-count cell.
- Preserve request construction, retry handling, pagination, empty input behavior, cached category thread reuse, nested thread-table filtering, description pager filtering, title/description extraction, successful post-count values, direct thread lookup, post access, and reply behavior.

## Type Of Change

- Bug fix / diagnostics improvement
- Forum thread-list parser error-context ergonomics
- Test addition

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| Malformed forum thread-list post-count text fails with wikidot.py's contextual parser exception rather than a raw integer conversion exception. | `TestForumThreadCollectionAcquireAll.test_acquire_all_malformed_post_count_includes_category_context` asserts `NoElementException` for a malformed `posts` count cell. | A raw `ValueError`, silent coercion, fabricated zero, or skipped thread rejects this local completion claim. |
| The malformed count error identifies the affected site, category, page, structural row, field, and raw value. | The focused test asserts `Posts count is malformed for site: test-site (category=1001, page=1, row=1, field=posts, value=not-a-number)`. | Omitting site, category, page, row, field, or value makes the failure ambiguous and rejects this local completion claim. |
| Successful thread-list count parsing remains unchanged. | `TestForumThreadCollectionParseListInCategory.test_parse_fields` still asserts `post_count == 5`; the full forum-thread unit file passed 47 tests. | Changing successful post counts, thread order, title/description text, pagination, cached category-thread behavior, or direct thread lookup rejects this local completion claim. |
| Adjacent forum workflows remain green. | `uv run pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed 168 tests. | Regressions in category, thread, post, or post-revision parsing and acquisition reject this local completion claim. |
| Broad unit and static quality gates remain green. | `uv run pytest tests/unit -q`; `uv run ruff check`; `uv run ruff format --check`; `uv run mypy src tests`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject this local completion claim. |

## Testing

Implemented locally in commit `d78dc35 fix(forum_thread): report malformed post count context`.

- RED: `uv run pytest tests/unit/test_forum_thread.py -k malformed_post_count_includes_category_context` failed before the fix with raw `ValueError` from `post_count=int(posts_count_elem.text)`.
- GREEN: `uv run pytest tests/unit/test_forum_thread.py -k malformed_post_count_includes_category_context` passed 1 test.
- `uv run pytest tests/unit/test_forum_thread.py` passed 47 tests.
- `uv run pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed 168 tests.
- `uv run pytest tests/unit -q` passed 778 tests.
- `uv run ruff format src/wikidot/module/forum_thread.py tests/unit/test_forum_thread.py` left 2 files unchanged.
- `uv run ruff check`.
- `uv run ruff format --check`.
- `uv run mypy src tests`.
- `git diff --check`.

Not run successfully: `uv run pyright --version` because this environment could not find a `pyright` executable.

## Acceptance Criteria

- A category thread-list response whose structural thread row has non-integer post-count text raises `NoElementException`.
- The malformed count message includes the site `unix_name`, category ID, page number, structural row index, affected field, and raw malformed value.
- Successful category thread-list parsing, retry behavior, pagination, empty input behavior, cached category thread reuse, nested thread-table filtering, description pager filtering, title/description text spacing, direct thread lookup, post access, and reply behavior remain unchanged.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Forum thread-list inspection is a read-heavy prerequisite for post and revision collection. When Wikidot returns malformed generated category thread-list markup, wikidot.py should still fail instead of inventing thread counts, but the failure should identify the affected category, page, row, field, and value so maintainers can triage from logs without storing raw generated HTML or rendered thread descriptions.

## Local Evidence, Not For Upstream Paste

- Earlier local drafts established category thread lists as a practical read-heavy workflow, including retry-aware category thread-list fetches, structural parser boundaries, nested thread-table filtering, description pager filtering, title/description text spacing, row-level parse context, and response-body validation.
- The refreshed complexity scanner continued to flag `src/wikidot/module/forum_thread.py` as a parser/acquisition hotspot after Issue 233 closed the adjacent forum-category count parser gap.
- The adjacent forum-category count-context slice showed the same pattern improves plain-text logs without changing successful parser output or live Wikidot behavior.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, raw category thread-list HTML, and thread contents out of upstream discussion.

## Additional Notes

This slice intentionally does not change `ForumThreadCollection.acquire_all_in_category(...)` request construction, retry handling, pagination, cache assignment, successful parser output, nested thread-table filtering, description pager filtering, title/description extraction, direct thread lookup, `ForumThread.posts`, `ForumThread.reply(...)`, or live Wikidot behavior. It only converts malformed category thread-list post-count values into contextual parser errors.
