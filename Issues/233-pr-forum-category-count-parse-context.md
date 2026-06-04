# PR Draft: Include Context In Forum Category Count Parse Errors

## Summary

`ForumCategoryCollection.acquire_all(...)`, used by `site.forum.categories`, parses forum category rows returned by `forum/ForumStartModule`. Earlier parser hardening added site and structural row context for missing category cells and other malformed row shapes, but malformed thread-count or post-count text still reached raw `int(...)` conversion and raised a bare `ValueError`.

This follow-up keeps successful parsing and existing `NoElementException` behavior for malformed Wikidot-generated category markup, but routes malformed category count values through the same contextual parser-error surface. The raised message now identifies the site, structural row, affected count field, and raw value, so plain-text logs can explain which forum-start row failed without preserving raw HTML.

## Related Issue

Builds on [033-pr-retry-forum-category-list-fetches.md](033-pr-retry-forum-category-list-fetches.md), [086-pr-ignore-nested-category-tables.md](086-pr-ignore-nested-category-tables.md), [108-pr-preserve-forum-category-description-spacing.md](108-pr-preserve-forum-category-description-spacing.md), [111-pr-preserve-forum-category-title-spacing.md](111-pr-preserve-forum-category-title-spacing.md), [157-pr-forum-category-parse-context.md](157-pr-forum-category-parse-context.md), and [211-pr-forum-category-list-response-body-context.md](211-pr-forum-category-list-response-body-context.md). Those drafts established retry-aware forum-category acquisition, structural parser boundaries, title/description preservation, row-level parse context, and response-body validation.

No upstream issue was filed from this local workspace.

## Changes

- Add a small forum-category count parser that converts count cell text to `int` and raises `NoElementException` on malformed values.
- Include site, structural row index, count field, and raw count value in malformed thread-count and post-count errors.
- Extend forum-category parser tests to cover malformed thread-count and post-count cells.
- Preserve request construction, retry handling, empty forum indexes, nested category-table filtering, title/description extraction, successful count values, category thread access, and thread creation behavior.

## Type Of Change

- Bug fix / diagnostics improvement
- Forum category parser error-context ergonomics
- Test addition

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| Malformed forum category count text fails with wikidot.py's contextual parser exception rather than a raw integer conversion exception. | `TestForumCategoryCollectionAcquireAll.test_acquire_all_malformed_count_includes_site_context` asserts `NoElementException` for malformed `threads` and `posts` count cells. | A raw `ValueError`, silent coercion, fabricated zero, or skipped category rejects this local completion claim. |
| The malformed count error identifies the affected site, structural row, field, and raw value. | The focused test asserts `Thread count is malformed for site: test-site (row=1, field=threads, value=not-a-number)` and `Post count is malformed for site: test-site (row=1, field=posts, value=bad-count)`. | Omitting site, row, field, or value makes the failure ambiguous and rejects this local completion claim. |
| Successful category count parsing remains unchanged. | `TestForumCategoryCollectionAcquireAll.test_acquire_all_parse_fields` still asserts `threads_count == 10` and `posts_count == 50`; the full forum-category unit file passed 22 tests. | Changing successful count values, category order, title/description text, empty results, or nested-table filtering rejects this local completion claim. |
| Adjacent forum workflows remain green. | `uv run pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed 167 tests. | Regressions in category, thread, post, or post-revision parsing and acquisition reject this local completion claim. |
| Broad unit and static quality gates remain green. | `uv run pytest tests/unit -q`; `uv run ruff check`; `uv run ruff format --check`; `uv run mypy src tests`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject this local completion claim. |

## Testing

Implemented locally in commit `39ea5c7 fix(forum_category): report malformed count context`.

- RED: `uv run pytest tests/unit/test_forum_category.py -k malformed_count_includes_site_context` failed before the fix with raw `ValueError` from `int(thread_count_elem.text)` and `int(post_count_elem.text)`.
- GREEN: `uv run pytest tests/unit/test_forum_category.py -k malformed_count_includes_site_context` passed 2 tests.
- `uv run pytest tests/unit/test_forum_category.py` passed 22 tests.
- `uv run pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed 167 tests.
- `uv run pytest tests/unit -q` passed 777 tests.
- `uv run ruff check`.
- `uv run ruff format --check`.
- `uv run mypy src tests`.
- `git diff --check`.

Not run successfully: `uv run pyright --version` because this environment could not find a `pyright` executable.

## Acceptance Criteria

- A forum category response whose structural category row has non-integer thread-count text raises `NoElementException`.
- A forum category response whose structural category row has non-integer post-count text raises `NoElementException`.
- Both malformed count messages include the site `unix_name`, structural row index, affected count field, and raw malformed value.
- Successful category parsing, retry behavior, empty forum indexes, nested category-table filtering, title/description text spacing, category field values, category thread access, and thread creation action payloads remain unchanged.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Forum category inspection is a read-heavy prerequisite for thread, post, and revision collection. When Wikidot returns malformed generated forum-start markup, wikidot.py should still fail instead of inventing categories, but the failure should identify the affected count field and value so maintainers can triage from logs without storing raw forum-start HTML or rendered category descriptions.

## Local Evidence, Not For Upstream Paste

- Earlier local drafts established forum categories as a practical read-heavy workflow, including retry-aware category-list fetches, structural parser boundaries, nested category-table filtering, title/description text spacing, and row-level parse context.
- Recent parser and direct-property context work showed that target-specific errors improve plain-text logs and resumable ledgers without changing successful behavior.
- The refreshed complexity memo continued to list `src/wikidot/module/forum_category.py` as an audit-worthy parser/acquisition surface after the scanner flagged the category acquisition loops.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, raw forum-start HTML, and category contents out of upstream discussion.

## Additional Notes

This slice intentionally does not change `ForumCategoryCollection.acquire_all(...)` request construction, retry handling, empty result handling, successful parser output, nested category-table filtering, title/description extraction, category field values, `ForumCategory.threads`, `ForumCategory.reload_threads()`, `ForumCategory.create_thread(...)`, or live Wikidot behavior. It only converts malformed forum-category count values into contextual parser errors.
