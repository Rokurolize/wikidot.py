# PR Draft: Report Malformed Forum Post Revision IDs

## Summary

`ForumPostRevisionCollection.acquire_all(...)` parses Wikidot's forum post revision list and returns the oldest-first `ForumPostRevision` collection for a post. When an otherwise valid revision row contained a direct `showRevision(...)` link whose revision ID token was malformed, the parser treated the regex miss the same as an absent revision link and silently skipped the row. Callers could receive an incomplete revision history with no site, post, row, field, or observed value explaining the loss.

This follow-up keeps the existing skip behavior for genuinely incomplete/non-revision rows, but raises `NoElementException` when a direct revision link is present and its `showRevision(...)` revision ID cannot be parsed. The error includes site `unix_name`, post ID, structural row number, `field=revision_id`, and the raw `onclick` value. Successful revision parsing, oldest-first `rev_no` assignment, direct-cell scoping, cached revision reuse, duplicate revision ID handling, retry-aware fetching, and revision HTML batching remain unchanged.

## Related Issue

Builds on [042-pr-retry-forum-post-revision-fetches.md](042-pr-retry-forum-post-revision-fetches.md), [056-pr-deduplicate-forum-post-revision-fetches.md](056-pr-deduplicate-forum-post-revision-fetches.md), [057-pr-deduplicate-forum-post-revision-html-fetches.md](057-pr-deduplicate-forum-post-revision-html-fetches.md), [058-pr-deduplicate-forum-post-revision-with-html-fetches.md](058-pr-deduplicate-forum-post-revision-with-html-fetches.md), [085-pr-scope-forum-revision-metadata.md](085-pr-scope-forum-revision-metadata.md), [121-pr-forum-post-revision-response-body-context.md](121-pr-forum-post-revision-response-body-context.md), and [133-pr-cache-direct-forum-post-revision-acquisition.md](133-pr-cache-direct-forum-post-revision-acquisition.md). Those drafts established forum post revision history as a practical rollback/audit surface with retry handling, deduplicated revision and HTML fetches, direct-cell parser scoping, response-body validation, and cache reuse.

No upstream issue was filed from this local workspace.

## Changes

- Add a small forum-post-revision list parse-context helper.
- Keep missing/non-revision row pieces on the existing skip path.
- Convert present-but-malformed `showRevision(...)` revision ID links into contextual `NoElementException`.
- Include site `unix_name`, post ID, row number, `field=revision_id`, and the raw `onclick` value, such as `value=WIKIDOT.modules.ForumViewThreadModule.listeners.showRevision(event, latest)`.
- Preserve successful revision list parsing, oldest-first ordering, `rev_no` assignment, nested metadata scoping, retry-aware acquisition, cached revision reuse, duplicate post ID handling, duplicate revision ID HTML fetch deduplication, and HTML acquisition semantics.
- Add a focused public `ForumPostRevisionCollection.acquire_all(...)` regression for malformed revision IDs.

## Type Of Change

- Bug fix / diagnostics improvement
- Forum post revision parser hardening
- Test addition

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| A structural forum post revision row with a direct `showRevision(...)` link but malformed revision ID fails instead of silently disappearing from the collection. | `TestForumPostRevisionCollectionAcquireAll.test_acquire_all_malformed_revision_id_includes_post_row_and_value_context` changes `showRevision(event, 9003)` to `showRevision(event, latest)` and expects `NoElementException`. | Returning a shorter successful collection, fabricating a revision ID, or leaking an unrelated exception rejects this local completion claim. |
| Malformed revision ID errors identify the affected site, post, row, field, and observed `onclick` value. | The focused regression asserts `Forum post revision ID is malformed for site: test-site, post: 5001 (row=1, field=revision_id, value=WIKIDOT.modules.ForumViewThreadModule.listeners.showRevision(event, latest))`. | Omitting site, post, row, field name, or raw value makes the failure ambiguous and rejects this local completion claim. |
| Successful revision list parsing stays intact. | The focused GREEN run includes `TestForumPostRevisionCollectionParse.test_parse_success`. | Changing revision count, IDs, oldest-first order, or `rev_no` assignment rejects this local completion claim. |
| Existing direct-cell scoping and duplicate revision HTML batching stay intact. | The focused GREEN run includes `TestForumPostRevisionCollectionParse.test_parse_uses_revision_cells_for_metadata` and `TestForumPostRevisionCollectionAcquireAllForPosts.test_acquire_all_for_posts_with_html_deduplicates_duplicate_revision_ids`. | Regressing nested metadata isolation or duplicate revision HTML fetch deduplication rejects this local completion claim. |
| Adjacent forum post and thread workflows remain green. | `uv run --extra test pytest tests/unit/test_forum_post_revision.py tests/unit/test_forum_post.py tests/unit/test_forum_thread.py -q` passed 155 tests. | Regressions in forum post parsing, revision acquisition, source fetching, edit handling, thread parsing, or direct thread fetching reject this local completion claim. |
| Broad unit and static quality gates remain green in the repo dependency environment. | `uv run --extra test pytest tests/unit/ -q`; `uv run --extra lint ruff check src tests`; `uv run --extra format ruff format --check src tests`; `uv run --extra lint mypy src tests --install-types --non-interactive`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject this local completion claim. |

## Testing

Implemented locally in commit `ada4827 fix(forum): report malformed revision IDs`.

- RED: `uv run --extra test pytest tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionAcquireAll::test_acquire_all_malformed_revision_id_includes_post_row_and_value_context -q` failed before the fix because the malformed `showRevision(event, latest)` row was silently skipped and no `NoElementException` was raised.
- GREEN: `uv run --extra test pytest tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionAcquireAll::test_acquire_all_malformed_revision_id_includes_post_row_and_value_context tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionParse::test_parse_success tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionParse::test_parse_uses_revision_cells_for_metadata tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionAcquireAllForPosts::test_acquire_all_for_posts_with_html_deduplicates_duplicate_revision_ids -q` passed 4 tests.
- `uv run --extra test pytest tests/unit/test_forum_post_revision.py -q` passed 44 tests.
- `uv run --extra test pytest tests/unit/test_forum_post_revision.py tests/unit/test_forum_post.py tests/unit/test_forum_thread.py -q` passed 155 tests.
- `uv run --extra test pytest tests/unit/ -q` passed 841 tests.
- `uv run --extra lint ruff check src tests`.
- `uv run --extra format ruff format --check src tests`.
- `uv run --extra lint mypy src tests --install-types --non-interactive`.
- `git diff --check`.

Not run successfully: `command -v pyright` did not find a `pyright` executable.

## Acceptance Criteria

- `ForumPostRevisionCollection.acquire_all(...)` raises `NoElementException` when an otherwise valid revision-list row has a direct `showRevision(...)` link whose revision ID token is malformed.
- The exception includes site `unix_name`, post ID, structural row number, `field=revision_id`, and the raw `onclick` value.
- Rows that genuinely lack revision-list structure continue to follow the existing skip behavior.
- Valid revision rows still parse into oldest-first `ForumPostRevision` objects with stable `rev_no` values.
- Successful revision list parsing, nested metadata isolation, retry behavior, missing response-body diagnostics, cached revision reuse, duplicate post ID handling, duplicate revision ID HTML fetch deduplication, skipped failed HTML retry responses, and direct revision HTML access remain unchanged.
- No live Wikidot action, upstream Issue, upstream PR, or push is required for this local draft.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and the local implementation commit.
- The thread HTML report and complexity memo are refreshed after the docs commit.
- Secret and local-path leak checks over the new draft pass before finalizing the turn.

## Upstream-Safe Motivation

Forum post revision history is used for auditing, rollback decisions, and historical content retrieval. If Wikidot emits a malformed revision ID in a structural revision row, silently dropping that row makes the returned history incomplete without warning. Reporting the malformed `onclick` value with site/post/row context gives callers actionable diagnostics while preserving the permissive skip path for rows that are not revision entries.

## Local Evidence, Not For Upstream Paste

- Earlier local drafts repeatedly identified forum post revision history as a practical workflow for retry-aware acquisition, deduplicated revision-list and revision-HTML requests, direct-cell parser scoping, response-body validation, and cache reuse.
- This slice intentionally targets only malformed present revision ID links in forum post revision rows. It does not change request payloads, retry policy, missing body handling, revision HTML fetching, cached revision reuse, duplicate ID batching, valid revision parsing, row ordering, row skipping for genuinely incomplete rows, user parsing, timestamp parsing, forum post editing, thread fetching, or live Wikidot behavior.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, cookies, auth JSON, generated forum HTML, post source text, post titles from real sites, and private forum content out of upstream discussion.

## Additional Notes

This is a parser observability fix. It turns a silent data-loss path into a self-contained parser error only when the row already advertises itself as a revision row through a direct `showRevision(...)` link.
