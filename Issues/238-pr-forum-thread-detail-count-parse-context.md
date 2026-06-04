# PR Draft: Include Context In Forum Thread Detail Count Parse Errors

## Summary

`ForumThreadCollection.acquire_from_thread_ids(...)`, exposed through `Site.get_thread(...)`, `Site.get_threads(...)`, and `ForumThread.get_from_id(...)`, parses direct thread detail HTML returned by `forum/ForumViewThreadModule`. Earlier local slices made direct thread detail acquisition retry-aware, deduplicated duplicate thread IDs, scoped thread detail statistics to the structural block, preserved formatted description text and breadcrumb separators, added site/thread parser context, validated missing detail response bodies, and converted malformed category thread-list post-count values into contextual parser errors. One adjacent parser-value gap remained in the direct thread detail parser: when the generated statistics block contained a post-count label without digits, the parser raised `Post count is not found for site: ... (thread=...)` without the affected field or raw value.

This follow-up keeps successful direct thread parsing unchanged, but routes the thread detail post-count text through a small parser helper. Malformed direct thread-detail post counts now raise `NoElementException` with site, requested thread ID, optional category, affected field, and raw value context, so plain-text logs can identify the broken generated statistic without retaining raw thread HTML or rendered thread descriptions.

## Related Issue

Builds on [035-pr-retry-thread-detail-fetches.md](035-pr-retry-thread-detail-fetches.md), [060-pr-deduplicate-thread-detail-fetches.md](060-pr-deduplicate-thread-detail-fetches.md), [088-pr-scope-thread-detail-statistics.md](088-pr-scope-thread-detail-statistics.md), [104-pr-preserve-thread-detail-description-text.md](104-pr-preserve-thread-detail-description-text.md), [105-pr-preserve-thread-title-separators.md](105-pr-preserve-thread-title-separators.md), [159-pr-forum-thread-detail-parse-context.md](159-pr-forum-thread-detail-parse-context.md), [214-pr-forum-thread-response-body-context.md](214-pr-forum-thread-response-body-context.md), and [234-pr-forum-thread-list-count-parse-context.md](234-pr-forum-thread-list-count-parse-context.md). Those drafts established direct thread detail acquisition as a retry-aware, duplicate-aware, structurally scoped, diagnosable read path and established the adjacent count-value parser diagnostic pattern for category thread lists.

No upstream issue was filed from this local workspace.

## Changes

- Add a small direct thread-detail post-count parser that extracts the numeric count and raises `NoElementException` on malformed values.
- Extend the thread detail parse-context helper so malformed count values can include field and raw value details.
- Add a focused regression for `Number of posts: not-a-number` in direct thread detail HTML.
- Preserve request construction, retry behavior, duplicate thread-ID deduplication, response-body validation, thread ID mismatch checks, structural statistics scoping, successful post-count parsing, title extraction, description text extraction, category association, post access, and reply behavior.

## Type Of Change

- Bug fix / diagnostics improvement
- Forum thread-detail parser error-context ergonomics
- Test addition

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| Malformed direct thread-detail post-count text fails with a contextual parser exception. | `TestForumThreadCollectionAcquireFromIds.test_acquire_from_ids_malformed_post_count_includes_thread_and_value_context` asserts `NoElementException` for `Number of posts: not-a-number`. | A generic `Post count is not found`, silent coercion, fabricated zero, skipped thread, or malformed `ForumThread` rejects this local completion claim. |
| The malformed count error identifies the affected site, requested thread ID, field, and raw value. | The focused test asserts `Post count is malformed for site: test-site (thread=3001, field=posts, value=Number of posts: not-a-number)`. | Omitting site, requested thread ID, field, or raw value makes the failure ambiguous and rejects this local completion claim. |
| Successful direct thread-detail parsing remains unchanged. | `uv run pytest tests/unit/test_forum_thread.py -q` passed 48 tests, including successful detail parsing, title separator preservation, description text preservation, response-body validation, duplicate thread-ID deduplication, retry exhaustion, post access, and replies. | Regressions in successful post counts, parsed thread IDs, titles, descriptions, creator/date parsing, category association, duplicate handling, or reply behavior reject this local completion claim. |
| Adjacent forum workflows remain green. | `uv run pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed 171 tests. | Regressions in category, thread, post, or post-revision parsing and acquisition reject this local completion claim. |
| Broad unit and static quality gates remain green. | `uv run pytest tests/unit -q`; `uv run ruff check`; `uv run ruff format --check`; `uv run mypy src tests`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject this local completion claim. |

## Testing

Implemented locally in commit `2627e3b fix(forum_thread): report malformed detail post counts`.

- RED: `uv run pytest tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireFromIds::test_acquire_from_ids_malformed_post_count_includes_thread_and_value_context -q` failed before the fix because the parser raised `Post count is not found for site: test-site (thread=3001)` without field or raw value context.
- GREEN: `uv run pytest tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireFromIds::test_acquire_from_ids_malformed_post_count_includes_thread_and_value_context -q` passed 1 test.
- `uv run pytest tests/unit/test_forum_thread.py -q` passed 48 tests.
- `uv run pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed 171 tests.
- `uv run ruff format src/wikidot/module/forum_thread.py tests/unit/test_forum_thread.py` left 2 files unchanged.
- `uv run ruff check`.
- `uv run ruff format --check`.
- `uv run pytest tests/unit -q` passed 783 tests.
- `uv run mypy src tests`.
- `git diff --check`.

Not run successfully: `uv run pyright --version` because this environment could not find a `pyright` executable.

## Acceptance Criteria

- A direct thread-detail response whose structural statistics block contains non-numeric post-count text raises `NoElementException`.
- The malformed count message includes the site `unix_name`, requested thread ID, affected field, and raw malformed value.
- Successful direct thread parsing, retry-aware fetching, duplicate-ID handling, thread ID mismatch detection, structural statistics scoping, title separator preservation, description text spacing, category association, post access, and reply action payloads remain unchanged.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Direct thread lookup is a read-heavy prerequisite for discussion inspection, post collection, source/revision workflows, and moderation-oriented tooling. When Wikidot returns malformed generated thread detail statistics, wikidot.py should fail rather than inventing a post count, but the failure should identify the affected thread, field, and raw value so maintainers can triage from logs without storing raw forum HTML or rendered thread descriptions.

## Local Evidence, Not For Upstream Paste

- Earlier local drafts established direct thread detail acquisition as a practical read-heavy workflow, including retry-aware direct thread fetches, duplicate-ID deduplication, structural statistics scoping, visible description text preservation, breadcrumb title separator handling, site/thread parser context, and response-body validation.
- The adjacent category thread-list post-count slice showed the same value-context pattern improves plain-text diagnostics without changing successful parser output or live Wikidot behavior.
- The complexity scanner continues to flag `src/wikidot/module/forum_thread.py` as a parser/acquisition hotspot, but this slice deliberately avoids broad parser rewrites.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, raw forum HTML, and thread contents out of upstream discussion.

## Additional Notes

This slice intentionally does not change `ForumThreadCollection.acquire_from_thread_ids(...)` request construction, retry handling, duplicate-ID behavior, response-body validation, requested/parsed thread ID mismatch checks, successful parser output, title extraction, description extraction, statistics scoping, category thread-list acquisition, `ForumThread.posts`, `ForumThread.reply(...)`, or live Wikidot behavior. It only converts malformed direct thread-detail post-count values into contextual parser errors.
