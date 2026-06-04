# PR Draft: Include Thread Context In Forum Thread Detail Parse Errors

## Summary

`ForumThreadCollection.acquire_from_thread_ids(...)`, exposed through `Site.get_thread(...)`, `Site.get_threads(...)`, and `ForumThread.get_from_id(...)`, parses direct thread detail HTML returned by `forum/ForumViewThreadModule`. The parser already fails when generated thread detail markup is missing required breadcrumbs, description, statistics, user, date, post count, or script data, but those failures only named the missing element. A plain log line such as `Description block element is not found.` did not identify which site or requested thread ID produced the malformed shape.

This follow-up keeps the existing `NoElementException` failure behavior and thread output shape, but includes the affected site `unix_name`, requested thread ID, and optional category ID in thread-detail parser failures. It also adds requested/parsed thread IDs to the direct thread ID mismatch failure. That makes direct thread-detail parser failures diagnosable from plain-text logs without saving raw forum HTML or thread descriptions.

## Related Issue

Builds on [035-pr-retry-thread-detail-fetches.md](035-pr-retry-thread-detail-fetches.md), [060-pr-deduplicate-thread-detail-fetches.md](060-pr-deduplicate-thread-detail-fetches.md), [088-pr-scope-thread-detail-statistics.md](088-pr-scope-thread-detail-statistics.md), [104-pr-preserve-thread-detail-description-text.md](104-pr-preserve-thread-detail-description-text.md), and [105-pr-preserve-thread-title-separators.md](105-pr-preserve-thread-title-separators.md), because those drafts established direct thread detail acquisition, retry-aware reads, duplicate request avoidance, structural statistics scoping, and visible thread detail text fidelity as practical local workflows.

This is the direct thread-detail companion to [158-pr-forum-thread-list-parse-context.md](158-pr-forum-thread-list-parse-context.md), which added category/page/row context to category thread-list parser failures.

No upstream issue was filed from this local workspace.

## Changes

- Add a small direct thread-detail parse-context helper for site name, requested thread ID, and optional category ID.
- Pass the requested thread ID into `ForumThreadCollection._parse_thread_page(...)` from `ForumThreadCollection.acquire_from_thread_ids(...)`.
- Include the context in missing breadcrumbs, empty title, description block, statistics block, user, odate, post-count structure, script element, and script thread-ID `NoElementException` messages.
- Include site, requested thread ID, and parsed thread ID in direct thread ID mismatch failures.
- Add a focused malformed direct thread-detail regression that asserts `Description block element is not found for site: test-site (thread=3001)`.
- Preserve retry-aware direct thread fetching, duplicate-ID deduplication, normal thread detail parsing, title separator preservation, description text spacing, category thread lists, post access, and replies.

## Type Of Change

- Bug fix / diagnostics improvement
- Forum thread-detail parser error-context ergonomics
- Test addition

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| Malformed direct thread detail markup still fails when a required structural block is missing. | `TestForumThreadCollectionAcquireFromIds.test_acquire_from_ids_missing_description_block_includes_thread_context` still expects `NoElementException` when the detail response has `div.wrong-block` instead of `div.description-block`. | A change that silently accepts the malformed detail page, fabricates empty descriptions, or shifts parser output rejects this local completion claim. |
| The malformed detail error identifies the affected site and requested thread ID. | The focused test asserts `Description block element is not found for site: test-site (thread=3001)`. | The RED test failed before the fix because the exception message was only `Description block element is not found.` |
| Related direct thread-detail parser failures use the same context helper. | Source inspection of `src/wikidot/module/forum_thread.py` shows breadcrumbs, title, description, statistics, user, odate, post-count structure, script, and script thread-ID `NoElementException` messages all append the parse context. | A future partial context change that only updates the description-block failure would leave the other direct detail parser failures as generic log lines. |
| Requested thread ID mismatch failures identify both sides of the mismatch. | Source inspection of `ForumThreadCollection.acquire_from_thread_ids(...)` shows the mismatch message includes site, requested thread ID, and parsed thread ID. | A future generic mismatch message would again require raw response inspection to identify the requested item. |
| Direct thread-detail workflows remain green. | `uv run --extra test pytest tests/unit/test_forum_thread.py -q` passed 42 tests. | Regressions in normal parsing, retry-aware direct reads, duplicate-ID handling, title separator preservation, description spacing, category thread-list access, post access, or replies reject this local completion claim. |
| Adjacent forum workflows remain green. | `uv run --extra test pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed 146 tests. | Regressions in category, thread, post, or post-revision behavior reject this local completion claim. |
| Broad unit and static quality gates remain green. | `uv run pytest tests/unit -q`; `uv run ruff check`; `uv run ruff format --check`; `uv run mypy src tests --install-types --non-interactive`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject this local completion claim. |

## Testing

Implemented locally in commit `61ae2b1 fix(forum_thread): include context in detail parse errors`.

- RED: `uv run --extra test pytest tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireFromIds::test_acquire_from_ids_missing_description_block_includes_thread_context -q` failed before the fix because the parser raised `Description block element is not found.` without site or requested thread ID.
- GREEN: `uv run --extra test pytest tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireFromIds::test_acquire_from_ids_missing_description_block_includes_thread_context -q`
- `uv run --extra test pytest tests/unit/test_forum_thread.py -q` passed 42 tests.
- `uv run --extra test pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed 146 tests.
- `uv run pytest tests/unit -q` passed 718 tests.
- `uv run ruff check`
- `uv run ruff format --check`
- `uv run mypy src tests --install-types --non-interactive`
- `git diff --check`

Not run successfully: `uv run pyright` because this environment could not find a `pyright` executable.

## Acceptance Criteria

- A direct thread-detail response whose structural description block is missing still raises `NoElementException`.
- The raised malformed-detail message includes the site `unix_name` and requested thread ID.
- Other malformed direct thread-detail field failures also include the same site/thread context.
- Requested/parsed thread ID mismatch failures identify the site and both thread IDs.
- Successful direct thread parsing, retry-aware fetching, duplicate-ID handling, category association, title separator preservation, description text spacing, category thread-list parsing, post access, and reply action payloads remain unchanged.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Direct thread lookup is a read-heavy prerequisite for discussion inspection, post collection, and moderation-oriented tooling. When Wikidot returns malformed generated thread detail markup, wikidot.py should still fail instead of inventing thread data, but the failure should identify the affected site and requested thread so maintainers can triage from logs without storing raw forum HTML or rendered thread descriptions.

## Local Evidence, Not For Upstream Paste

- Earlier local drafts established direct thread detail acquisition as a practical read-heavy workflow, including retry-aware direct thread fetches, duplicate-ID deduplication, structural statistics scoping, visible description text preservation, and breadcrumb title separator handling.
- The preceding category thread-list parse-context slice showed that target-specific parser errors improve plain-text logs and resumable ledgers without changing successful behavior.
- The refreshed complexity memo continues to list `src/wikidot/module/forum_thread.py` as an audit-worthy parser/acquisition surface.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, raw forum HTML, and thread contents out of upstream discussion.

## Additional Notes

This slice intentionally does not change `ForumThreadCollection.acquire_from_thread_ids(...)` request construction, retry handling, duplicate-ID behavior, successful parser output, title extraction, description extraction, statistics scoping, post-count parsing, category thread-list acquisition, `ForumThread.posts`, `ForumThread.reply(...)`, or live Wikidot behavior. It only adds site/thread context to existing malformed direct thread-detail parse failures and direct thread-ID mismatch failures.
