# PR Draft: Ignore Private Message Nested Row Markup

## Summary

`PrivateMessageCollection._acquire(...)` extracts message IDs from inbox and sentbox list pages by reading `tr.message` rows, then delegates detail fetching to `PrivateMessageCollection.from_ids(...)`.

Before this fix, row discovery selected `tr.message` response-wide. If a message-list row preview rendered nested table markup containing another `tr.message`, the acquisition path treated that nested row as a second real private message. The focused regression inserted a fake nested `tr.message` with ID `999` inside the real message row for ID `123`; before the fix, `from_ids(...)` received `[123, 999]`.

This fix keeps real private-message list rows unchanged, but ignores `tr.message` candidates nested inside another message row.

## Related Issue

Builds on [037-pr-retry-private-message-fetches.md](037-pr-retry-private-message-fetches.md), [054-pr-deduplicate-private-message-detail-fetches.md](054-pr-deduplicate-private-message-detail-fetches.md), [067-pr-deduplicate-direct-private-message-fetches.md](067-pr-deduplicate-direct-private-message-fetches.md), [073-pr-reuse-private-message-detail-parsing.md](073-pr-reuse-private-message-detail-parsing.md), [077-pr-skip-empty-private-message-fetch-batches.md](077-pr-skip-empty-private-message-fetch-batches.md), and [101-pr-ignore-private-message-row-pager-markup.md](101-pr-ignore-private-message-row-pager-markup.md), because those drafts established private-message acquisition as a practical local workflow and message rows as content-adjacent parser boundaries.

The row-boundary failure class is adjacent to [081-pr-ignore-forum-content-pseudo-posts.md](081-pr-ignore-forum-content-pseudo-posts.md), [083-pr-ignore-content-post-containers.md](083-pr-ignore-content-post-containers.md), [086-pr-ignore-nested-category-tables.md](086-pr-ignore-nested-category-tables.md), [087-pr-ignore-nested-thread-tables.md](087-pr-ignore-nested-thread-tables.md), [094-pr-scope-page-revision-row-cells.md](094-pr-scope-page-revision-row-cells.md), [095-pr-scope-page-file-row-parsing.md](095-pr-scope-page-file-row-parsing.md), [096-pr-scope-site-member-row-parsing.md](096-pr-scope-site-member-row-parsing.md), and [101-pr-ignore-private-message-row-pager-markup.md](101-pr-ignore-private-message-row-pager-markup.md): all of these fixes prevent nested content-like markup from becoming structural records or structural controls.

No upstream issue was filed from this local workspace.

## Changes

- Skip `tr.message` candidates whose ancestor chain already contains a `tr.message`.
- Reuse the existing `PrivateMessageCollection._is_inside_message_row(...)` helper added for pager-boundary filtering.
- Add a regression where a nested fake `tr.message` inside a real message row does not add a fake message ID.
- Preserve normal message ID extraction, missing/malformed `data-href` errors for structural rows, first-page retry handling, real pagination, non-numeric pager handling, row-pager filtering, paginated retry error handling, duplicate ID preservation semantics, and detail-fetch delegation.

## Type Of Change

- Bug fix
- Parser robustness improvement
- Test addition/modification

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| Nested `tr.message` markup inside a private-message row should not be treated as another inbox/sentbox message. | `TestPrivateMessageCollection.test_acquire_ignores_nested_message_row_markup` inserts nested fake message row ID `999` inside real row ID `123` and asserts `from_ids(...)` receives `[123]`. | The RED test failed before the fix because `from_ids(...)` received `[123, 999]`. |
| Real structural private-message rows and pagination should continue to work. | The neighboring PM acquisition tests, including non-numeric pager, row-pager filtering, paginated deduplication, and exhausted paginated retry handling, remained green. | If a real structural row is skipped or real structural pagination stops queuing page 2, the focused neighboring tests reject the local completion claim. |
| Existing private-message and client workflows should remain green. | `uv run pytest tests/unit/test_private_message.py -q` passed 29 tests, and `uv run pytest tests/unit/test_private_message.py tests/unit/test_client.py -q` passed 48 tests. | Regressions in message detail parsing, deduplication, retry behavior, inbox/sentbox factories, or client private-message accessors reject the local completion claim. |
| Broad unit and static quality gates remain green. | `uv run pytest tests/unit -q`; `uv run ruff check .`; `uv run ruff format --check .`; `uv run mypy .`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject the local completion claim. |

## Testing

Implemented locally in commit `aa8b0ec fix(private_message): ignore nested row markup`.

- RED: `uv run pytest tests/unit/test_private_message.py::TestPrivateMessageCollection::test_acquire_ignores_nested_message_row_markup -q` failed before the fix because `from_ids(...)` received `[123, 999]`.
- GREEN: `uv run pytest tests/unit/test_private_message.py::TestPrivateMessageCollection::test_acquire_ignores_nested_message_row_markup -q`
- `uv run pytest tests/unit/test_private_message.py::TestPrivateMessageCollection::test_acquire_ignores_non_numeric_pager_targets tests/unit/test_private_message.py::TestPrivateMessageCollection::test_acquire_ignores_message_row_pager_markup tests/unit/test_private_message.py::TestPrivateMessageCollection::test_acquire_ignores_nested_message_row_markup tests/unit/test_private_message.py::TestPrivateMessageCollection::test_acquire_deduplicates_message_ids_preserving_order tests/unit/test_private_message.py::TestPrivateMessageCollection::test_acquire_raises_when_paginated_retry_is_exhausted -q` passed 5 tests.
- `uv run pytest tests/unit/test_private_message.py -q` passed 29 tests.
- `uv run pytest tests/unit/test_private_message.py tests/unit/test_client.py -q` passed 48 tests.
- `uv run pytest tests/unit -q` passed 654 tests.
- `uv run ruff check .`
- `uv run ruff format --check .`
- `uv run mypy .`
- `git diff --check`

Not run: `uv run pyright src tests` because this environment could not find a `pyright` executable on PATH in earlier checks.

## Acceptance Criteria

- `tr.message` markup nested inside another `tr.message` row is treated as message-list row content only.
- Nested fake message rows cannot add fake message IDs to `from_ids(...)`.
- Real structural message rows still produce message IDs.
- Real structural inbox/sentbox pagination still queues additional pages.
- Missing or malformed `data-href` on structural rows still raises the existing errors.
- Existing first-page retry handling, additional-page retry failure behavior, duplicate message ID preservation, row-pager filtering, empty input behavior, detail parsing, inbox/sentbox factories, and client private-message accessors remain unchanged.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Private-message list rows are structural records, but row preview/body-adjacent markup can contain table-like content. `PrivateMessageCollection._acquire(...)` should only treat top-level message-list rows as private-message records and ignore nested row-like markup inside an existing message row.

## Local Evidence, Not For Upstream Paste

- Earlier local drafts [037-pr-retry-private-message-fetches.md](037-pr-retry-private-message-fetches.md), [054-pr-deduplicate-private-message-detail-fetches.md](054-pr-deduplicate-private-message-detail-fetches.md), [067-pr-deduplicate-direct-private-message-fetches.md](067-pr-deduplicate-direct-private-message-fetches.md), [073-pr-reuse-private-message-detail-parsing.md](073-pr-reuse-private-message-detail-parsing.md), [077-pr-skip-empty-private-message-fetch-batches.md](077-pr-skip-empty-private-message-fetch-batches.md), and [101-pr-ignore-private-message-row-pager-markup.md](101-pr-ignore-private-message-row-pager-markup.md) established private-message acquisition as a practical local target and `tr.message` rows as an audited boundary.
- Parser-boundary drafts [081-pr-ignore-forum-content-pseudo-posts.md](081-pr-ignore-forum-content-pseudo-posts.md), [083-pr-ignore-content-post-containers.md](083-pr-ignore-content-post-containers.md), [086-pr-ignore-nested-category-tables.md](086-pr-ignore-nested-category-tables.md), [087-pr-ignore-nested-thread-tables.md](087-pr-ignore-nested-thread-tables.md), [094-pr-scope-page-revision-row-cells.md](094-pr-scope-page-revision-row-cells.md), [095-pr-scope-page-file-row-parsing.md](095-pr-scope-page-file-row-parsing.md), and [096-pr-scope-site-member-row-parsing.md](096-pr-scope-site-member-row-parsing.md) established the same nested-row/table failure pattern on adjacent modules.
- The refreshed complexity scan continues to flag private-message parsing/request loops as audit-worthy paths, and the PM list path still had response-wide message-row discovery before this fix.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, and message contents out of upstream discussion.

## Additional Notes

This slice does not change request construction, retry policy, batch sizing, pager parsing, `data-href` ID extraction, duplicate message ID handling, message detail parsing, inbox/sentbox wrappers, or the `PrivateMessage` dataclass. It only narrows message-row discovery before detail requests are delegated to `from_ids(...)`.
