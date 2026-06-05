# PR Draft: Report Malformed Forum Post Revision Timestamps

## Summary

`ForumPostRevisionCollection.acquire_all(...)` parses Wikidot's forum post revision list and converts each direct revision row's `span.odate` into `ForumPostRevision.created_at`. When the timestamp element existed but carried a malformed `time_...` class, the shared `odate_parse(...)` utility raised a raw `ValueError` such as `invalid literal for int()`, without identifying the site, forum post, structural revision-list row, affected field, or observed class value.

This follow-up keeps the shared `odate` parser behavior unchanged, but catches malformed timestamp values at the forum post revision-list parser boundary and raises `NoElementException` with site `unix_name`, post ID, row number, `field=created_at`, and the offending `time_...` class. Successful revision parsing, oldest-first `rev_no` assignment, direct-cell scoping, malformed revision ID diagnostics, cached revision reuse, duplicate revision ID handling, retry-aware fetching, and revision HTML batching remain unchanged.

## Related Issue

Builds on [042-pr-retry-forum-post-revision-fetches.md](042-pr-retry-forum-post-revision-fetches.md), [056-pr-deduplicate-forum-post-revision-fetches.md](056-pr-deduplicate-forum-post-revision-fetches.md), [057-pr-deduplicate-forum-post-revision-html-fetches.md](057-pr-deduplicate-forum-post-revision-html-fetches.md), [058-pr-deduplicate-forum-post-revision-with-html-fetches.md](058-pr-deduplicate-forum-post-revision-with-html-fetches.md), [085-pr-scope-forum-revision-metadata.md](085-pr-scope-forum-revision-metadata.md), [121-pr-forum-post-revision-response-body-context.md](121-pr-forum-post-revision-response-body-context.md), [133-pr-cache-direct-forum-post-revision-acquisition.md](133-pr-cache-direct-forum-post-revision-acquisition.md), and [283-pr-forum-post-revision-id-context.md](283-pr-forum-post-revision-id-context.md). Those drafts established forum post revision history as a practical rollback/audit surface with retry handling, deduplicated revision and HTML fetches, direct-cell parser scoping, response-body validation, cache reuse, and contextual malformed revision ID diagnostics.

No upstream issue was filed from this local workspace.

## Changes

- Preserve the existing skip behavior for rows that genuinely lack revision-list structure.
- Convert malformed forum post revision timestamp class values from raw `ValueError` into contextual `NoElementException`.
- Include site `unix_name`, post ID, row number, `field=created_at`, and the offending `time_...` class, such as `value=time_latest`.
- Preserve the shared `odate_parse(...)` utility behavior and parser tests.
- Preserve successful revision list parsing, oldest-first ordering, `rev_no` assignment, nested metadata scoping, malformed revision ID diagnostics, retry-aware acquisition, cached revision reuse, duplicate post ID handling, duplicate revision ID HTML fetch deduplication, and HTML acquisition semantics.
- Add a focused public `ForumPostRevisionCollection.acquire_all(...)` regression for malformed timestamp classes.

## Type Of Change

- Bug fix / diagnostics improvement
- Forum post revision parser hardening
- Test addition

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| A structural forum post revision row whose direct `span.odate` has a malformed `time_...` class fails at the revision-list parser boundary. | `TestForumPostRevisionCollectionAcquireAll.test_acquire_all_malformed_odate_includes_post_row_and_value_context` changes `time_1700000300` to `time_latest` and expects `NoElementException`. | Leaking raw `ValueError`, fabricating a timestamp, or silently dropping the row rejects this local completion claim. |
| Malformed timestamp errors identify the affected site, post, row, field, and bad class value. | The focused regression asserts `Forum post revision timestamp is malformed for site: test-site, post: 5001 (row=1, field=created_at, value=time_latest)`. | Omitting site, post, row, field name, or bad class value makes the failure ambiguous and rejects this local completion claim. |
| Successful revision list parsing stays intact. | The focused GREEN run includes `TestForumPostRevisionCollectionParse.test_parse_success`. | Changing revision count, IDs, oldest-first order, timestamps, or `rev_no` assignment rejects this local completion claim. |
| Existing malformed revision ID context and direct-cell scoping stay intact. | The focused GREEN run includes `TestForumPostRevisionCollectionAcquireAll.test_acquire_all_malformed_revision_id_includes_post_row_and_value_context` and `TestForumPostRevisionCollectionParse.test_parse_uses_revision_cells_for_metadata`. | Regressing the previous revision ID diagnostic fix or nested metadata isolation rejects this local completion claim. |
| Adjacent forum post and thread workflows remain green. | `uv run --extra test pytest tests/unit/test_forum_post_revision.py tests/unit/test_forum_post.py tests/unit/test_forum_thread.py -q` passed 156 tests. | Regressions in forum post parsing, revision acquisition, source fetching, edit handling, thread parsing, or direct thread fetching reject this local completion claim. |
| Broad unit and static quality gates remain green in the repo dependency environment. | `uv run --extra test pytest tests/unit/ -q`; `uv run --extra lint ruff check src tests`; `uv run --extra format ruff format --check src tests`; `uv run --extra lint mypy src tests --install-types --non-interactive`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject this local completion claim. |

## Testing

Implemented locally in commit `78a97d3 fix(forum): report malformed revision timestamps`.

- RED: `uv run --extra test pytest tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionAcquireAll::test_acquire_all_malformed_odate_includes_post_row_and_value_context -q` failed before the fix because a malformed `time_latest` class leaked `ValueError: invalid literal for int() with base 10: 'latest'`.
- GREEN: `uv run --extra test pytest tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionAcquireAll::test_acquire_all_malformed_odate_includes_post_row_and_value_context tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionAcquireAll::test_acquire_all_malformed_revision_id_includes_post_row_and_value_context tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionParse::test_parse_success tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionParse::test_parse_uses_revision_cells_for_metadata -q` passed 4 tests.
- `uv run --extra test pytest tests/unit/test_forum_post_revision.py -q` passed 45 tests.
- `uv run --extra test pytest tests/unit/test_forum_post_revision.py tests/unit/test_forum_post.py tests/unit/test_forum_thread.py -q` passed 156 tests.
- `uv run --extra test pytest tests/unit/ -q` passed 842 tests.
- `uv run --extra lint ruff check src tests`.
- `uv run --extra format ruff format --check src tests`.
- `uv run --extra lint mypy src tests --install-types --non-interactive`.
- `git diff --check`.

Not run successfully: `command -v pyright` did not find a `pyright` executable.

## Acceptance Criteria

- `ForumPostRevisionCollection.acquire_all(...)` raises `NoElementException` when an otherwise valid revision-list row has a direct `span.odate` whose `time_...` class is malformed.
- The exception includes site `unix_name`, post ID, structural row number, `field=created_at`, and the bad `time_...` class value.
- Rows that genuinely lack revision-list structure continue to follow the existing skip behavior.
- Valid revision rows still parse timestamps through the existing `odate_parse(...)` utility.
- Successful revision list parsing, nested metadata isolation, malformed revision ID diagnostics, retry behavior, missing response-body diagnostics, cached revision reuse, duplicate post ID handling, duplicate revision ID HTML fetch deduplication, skipped failed HTML retry responses, and direct revision HTML access remain unchanged.
- No live Wikidot action, upstream Issue, upstream PR, or push is required for this local draft.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and the local implementation commit.
- The thread HTML report and complexity memo are refreshed after the docs commit.
- Secret and local-path leak checks over the new draft pass before finalizing the turn.

## Upstream-Safe Motivation

Forum post revision timestamps are core audit fields for ordering historical edits and reconstructing post history. When Wikidot's generated module emits a malformed timestamp class, wikidot.py should report a structured parser failure that tells callers which post row and field failed, rather than leaking a raw integer conversion exception. Including the offending class value makes the failure actionable without requiring logs to retain generated forum HTML or private forum content.

## Local Evidence, Not For Upstream Paste

- Earlier local drafts repeatedly identified forum post revision history as a practical workflow for retry-aware acquisition, deduplicated revision-list and revision-HTML requests, direct-cell parser scoping, response-body validation, cache reuse, and contextual malformed revision ID diagnostics.
- This slice intentionally targets only malformed present timestamp classes in forum post revision rows. It does not change request payloads, retry policy, missing body handling, revision ID parsing, revision HTML fetching, cached revision reuse, duplicate ID batching, valid revision parsing, row ordering, row skipping for genuinely incomplete rows, user parsing, forum post editing, thread fetching, or live Wikidot behavior.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, cookies, auth JSON, generated forum HTML, post source text, post titles from real sites, and private forum content out of upstream discussion.

## Additional Notes

This is a parser observability fix. It keeps the valid timestamp path and common parser untouched while making malformed forum post revision timestamp rows self-contained enough for logs and audit ledgers.
