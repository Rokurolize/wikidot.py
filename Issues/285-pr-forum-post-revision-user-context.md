# PR Draft: Report Malformed Forum Post Revision Users

## Summary

`ForumPostRevisionCollection.acquire_all(...)` parses Wikidot's forum post revision list and converts each direct revision row's `span.printuser` into `ForumPostRevision.created_by`. When the user element existed but its direct `onclick` metadata did not contain a numeric `userInfo(...)` ID, the shared `user_parse(...)` utility raised raw `ValueError("user id is not found")`, without identifying the site, forum post, structural revision-list row, affected field, or observed `onclick` value.

This follow-up keeps the shared `user_parse(...)` utility behavior unchanged, but catches malformed present user metadata at the forum post revision-list parser boundary and raises `NoElementException` with site `unix_name`, post ID, row number, `field=created_by`, and the offending direct user `onclick` value. Successful revision parsing, oldest-first `rev_no` assignment, direct-cell scoping, malformed revision ID diagnostics, malformed timestamp diagnostics, cached revision reuse, duplicate revision ID handling, retry-aware fetching, and revision HTML batching remain unchanged.

## Related Issue

Builds on [042-pr-retry-forum-post-revision-fetches.md](042-pr-retry-forum-post-revision-fetches.md), [056-pr-deduplicate-forum-post-revision-fetches.md](056-pr-deduplicate-forum-post-revision-fetches.md), [057-pr-deduplicate-forum-post-revision-html-fetches.md](057-pr-deduplicate-forum-post-revision-html-fetches.md), [058-pr-deduplicate-forum-post-revision-with-html-fetches.md](058-pr-deduplicate-forum-post-revision-with-html-fetches.md), [085-pr-scope-forum-revision-metadata.md](085-pr-scope-forum-revision-metadata.md), [217-pr-forum-post-revision-response-body-context.md](217-pr-forum-post-revision-response-body-context.md), [229-pr-cache-direct-post-revision-acquisition.md](229-pr-cache-direct-post-revision-acquisition.md), [283-pr-forum-post-revision-id-context.md](283-pr-forum-post-revision-id-context.md), and [284-pr-forum-post-revision-timestamp-context.md](284-pr-forum-post-revision-timestamp-context.md). Those drafts established forum post revision history as a practical rollback/audit surface with retry handling, deduplicated revision and HTML fetches, direct-cell parser scoping, response-body validation, cache reuse, contextual malformed revision ID diagnostics, and contextual malformed timestamp diagnostics.

No upstream issue was filed from this local workspace.

## Changes

- Preserve the existing skip behavior for rows that genuinely lack revision-list structure.
- Convert malformed present forum post revision `printuser` metadata from raw `ValueError` into contextual `NoElementException`.
- Include site `unix_name`, post ID, row number, `field=created_by`, and the offending direct user `onclick` value, such as `value=WIKIDOT.page.listeners.userInfo(latest); return false;`.
- Preserve the shared `user_parse(...)` utility behavior and parser tests.
- Preserve successful revision list parsing, oldest-first ordering, `rev_no` assignment, nested metadata scoping, malformed revision ID diagnostics, malformed timestamp diagnostics, retry-aware acquisition, cached revision reuse, duplicate post ID handling, duplicate revision ID HTML fetch deduplication, and HTML acquisition semantics.
- Add a focused public `ForumPostRevisionCollection.acquire_all(...)` regression for malformed user metadata.

## Type Of Change

- Bug fix / diagnostics improvement
- Forum post revision parser hardening
- Test addition

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| A structural forum post revision row whose direct `span.printuser` has malformed `userInfo(...)` metadata fails at the revision-list parser boundary. | `TestForumPostRevisionCollectionAcquireAll.test_acquire_all_malformed_user_includes_post_row_and_value_context` changes `userInfo(99999)` to `userInfo(latest)` and expects `NoElementException`. | Leaking raw `ValueError`, fabricating a user, or silently dropping the row rejects this local completion claim. |
| Malformed user errors identify the affected site, post, row, field, and bad direct `onclick` value. | The focused regression asserts `Forum post revision user is malformed for site: test-site, post: 5001 (row=1, field=created_by, value=WIKIDOT.page.listeners.userInfo(latest); return false;)`. | Omitting site, post, row, field name, or bad `onclick` value makes the failure ambiguous and rejects this local completion claim. |
| Successful revision list parsing stays intact. | The focused GREEN run includes `TestForumPostRevisionCollectionParse.test_parse_success`. | Changing revision count, IDs, oldest-first order, user parsing, timestamps, or `rev_no` assignment rejects this local completion claim. |
| Existing malformed revision ID and malformed timestamp context stay intact. | The focused GREEN run includes `TestForumPostRevisionCollectionAcquireAll.test_acquire_all_malformed_revision_id_includes_post_row_and_value_context` and `TestForumPostRevisionCollectionAcquireAll.test_acquire_all_malformed_odate_includes_post_row_and_value_context`. | Regressing either adjacent parser diagnostic rejects this local completion claim. |
| Adjacent forum post and thread workflows remain green. | `uv run --extra test pytest tests/unit/test_forum_post_revision.py tests/unit/test_forum_post.py tests/unit/test_forum_thread.py -q` passed 157 tests. | Regressions in forum post parsing, revision acquisition, source fetching, edit handling, thread parsing, or direct thread fetching reject this local completion claim. |
| Broad unit and static quality gates remain green in the repo dependency environment. | `uv run --extra test pytest tests/unit/ -q`; `uv run --extra lint ruff check src tests`; `uv run --extra format ruff format --check src tests`; `uv run --extra lint mypy src tests --install-types --non-interactive`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject this local completion claim. |

## Testing

Implemented locally in commit `2737c56 fix(forum): report malformed revision users`.

- RED: `uv run --extra test pytest tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionAcquireAll::test_acquire_all_malformed_user_includes_post_row_and_value_context -q` failed before the fix because malformed `userInfo(latest)` metadata leaked raw `ValueError: user id is not found` from `user_parse(...)`.
- GREEN: `uv run --extra test pytest tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionAcquireAll::test_acquire_all_malformed_user_includes_post_row_and_value_context tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionAcquireAll::test_acquire_all_malformed_odate_includes_post_row_and_value_context tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionAcquireAll::test_acquire_all_malformed_revision_id_includes_post_row_and_value_context tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionParse::test_parse_success -q` passed 4 tests.
- `uv run --extra test pytest tests/unit/test_forum_post_revision.py -q` passed 46 tests.
- `uv run --extra test pytest tests/unit/test_forum_post_revision.py tests/unit/test_forum_post.py tests/unit/test_forum_thread.py -q` passed 157 tests.
- `uv run --extra test pytest tests/unit/ -q` passed 843 tests.
- `uv run --extra lint ruff check src tests`.
- `uv run --extra format ruff format --check src tests`.
- `uv run --extra lint mypy src tests --install-types --non-interactive`.
- `git diff --check`.

Not run successfully: `command -v pyright` did not find a `pyright` executable.

## Acceptance Criteria

- `ForumPostRevisionCollection.acquire_all(...)` raises `NoElementException` when an otherwise valid revision-list row has a direct `span.printuser` whose `userInfo(...)` metadata is malformed.
- The exception includes site `unix_name`, post ID, structural row number, `field=created_by`, and the bad direct user `onclick` value.
- Rows that genuinely lack revision-list structure continue to follow the existing skip behavior.
- Valid revision rows still parse users through the existing `user_parse(...)` utility.
- Successful revision list parsing, nested metadata isolation, malformed revision ID diagnostics, malformed timestamp diagnostics, retry behavior, missing response-body diagnostics, cached revision reuse, duplicate post ID handling, duplicate revision ID HTML fetch deduplication, skipped failed HTML retry responses, and direct revision HTML access remain unchanged.
- No live Wikidot action, upstream Issue, upstream PR, or push is required for this local draft.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and the local implementation commit.
- The thread HTML report and complexity memo are refreshed after the docs commit.
- Secret and local-path leak checks over the new draft pass before finalizing the turn.

## Upstream-Safe Motivation

Forum post revision users are core audit fields for identifying who edited a post. When Wikidot's generated module emits malformed direct user metadata, wikidot.py should report a structured parser failure that tells callers which post row and field failed, rather than leaking a raw helper exception. Including the offending `onclick` value makes the failure actionable without requiring logs to retain generated forum HTML or private forum content.

## Local Evidence, Not For Upstream Paste

- Earlier local drafts repeatedly identified forum post revision history as a practical workflow for retry-aware acquisition, deduplicated revision-list and revision-HTML requests, direct-cell parser scoping, response-body validation, cache reuse, and contextual malformed revision ID and timestamp diagnostics.
- This slice intentionally targets only malformed present direct `printuser` metadata in forum post revision rows. It does not change request payloads, retry policy, missing body handling, revision ID parsing, timestamp parsing, revision HTML fetching, cached revision reuse, duplicate ID batching, valid revision parsing, row ordering, row skipping for genuinely incomplete rows, shared user parsing, forum post editing, thread fetching, or live Wikidot behavior.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, cookies, auth JSON, generated forum HTML, post source text, post titles from real sites, and private forum content out of upstream discussion.

## Additional Notes

This is a parser observability fix. It keeps the valid user path and shared parser untouched while making malformed forum post revision user rows self-contained enough for logs and audit ledgers.
