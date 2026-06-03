# PR Draft: Ignore Private Message Row Pager Markup

## Summary

`PrivateMessageCollection._acquire(...)` fetches the first inbox or sentbox page, reads the page-list pager to decide whether additional message-list pages should be requested, then extracts message IDs from `tr.message` rows before fetching message details.

Before this fix, pagination discovery selected `div.pager span.target` response-wide. If message-row preview markup rendered pager-like content, the acquisition path treated that row content as structural inbox/sentbox pagination. The focused regression inserted a `div.pager` with numeric targets `1` and `2` inside a `tr.message` row; before the fix, the method made a phantom second AMC page request even though only one message-list page was present.

This fix keeps real private-message list pagination unchanged, but ignores pager elements nested inside message rows.

## Related Issue

Builds on [037-pr-retry-private-message-fetches.md](037-pr-retry-private-message-fetches.md), [054-pr-deduplicate-private-message-detail-fetches.md](054-pr-deduplicate-private-message-detail-fetches.md), [067-pr-deduplicate-direct-private-message-fetches.md](067-pr-deduplicate-direct-private-message-fetches.md), [073-pr-reuse-private-message-detail-parsing.md](073-pr-reuse-private-message-detail-parsing.md), and [077-pr-skip-empty-private-message-fetch-batches.md](077-pr-skip-empty-private-message-fetch-batches.md), because those drafts established private-message inbox, sentbox, and detail fetching as practical local workflows worth hardening.

The pagination failure class is adjacent to [097-pr-ignore-forum-content-pager-markup.md](097-pr-ignore-forum-content-pager-markup.md), [098-pr-ignore-thread-description-pager-markup.md](098-pr-ignore-thread-description-pager-markup.md), [099-pr-ignore-recent-change-comment-pager-markup.md](099-pr-ignore-recent-change-comment-pager-markup.md), and [100-pr-ignore-listpages-field-pager-markup.md](100-pr-ignore-listpages-field-pager-markup.md): all five fixes prevent content-adjacent markup from queueing extra AMC page requests while preserving structural pagers.

No upstream issue was filed from this local workspace.

## Changes

- Add `PrivateMessageCollection._pager_targets_from_html(...)` to return pager targets from the first structural PM-list pager outside message rows.
- Add `PrivateMessageCollection._is_inside_message_row(...)` to identify pager candidates nested under `tr.message`.
- Use the structural-pager helper before deriving the private-message list `max_page`.
- Add a regression where a message row containing `div.pager` with numeric targets does not trigger an additional inbox/sentbox page request.
- Preserve normal message ID extraction, first-page retry handling, real pagination, non-numeric pager handling, paginated retry error handling, duplicate ID preservation semantics, and detail-fetch delegation.

## Type Of Change

- Bug fix
- Parser robustness improvement
- Test addition/modification

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| Pager-like markup inside a private-message row should not be treated as inbox/sentbox pagination. | `TestPrivateMessageCollection.test_acquire_ignores_message_row_pager_markup` inserts a `div.pager` with numeric targets inside `tr.message`, asserts only one AMC request is made, and asserts `from_ids(...)` receives the real message ID. | The RED test failed before the fix because `client.amc_client.request.call_count` was `2` after a phantom second-page fetch. |
| Real structural private-message pagination should continue to request additional pages. | `test_acquire_deduplicates_message_ids_preserving_order` and `test_acquire_raises_when_paginated_retry_is_exhausted` remained green with the focused pager regression. | If a real structural pager stops queuing page 2, the existing pagination tests reject the local completion claim. |
| Existing private-message and client workflows should remain green. | `uv run pytest tests/unit/test_private_message.py -q` passed 28 tests, and `uv run pytest tests/unit/test_private_message.py tests/unit/test_client.py -q` passed 47 tests. | Regressions in message detail parsing, deduplication, retry behavior, inbox/sentbox factories, or client private-message accessors reject the local completion claim. |
| Broad unit and static quality gates remain green. | `uv run pytest tests/unit -q`; `uv run ruff check .`; `uv run ruff format --check .`; `uv run mypy .`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject the local completion claim. |

## Testing

Implemented locally in commit `0e1d08a fix(private_message): ignore row pager markup`.

- RED: `uv run pytest tests/unit/test_private_message.py::TestPrivateMessageCollection::test_acquire_ignores_message_row_pager_markup -q` failed before the fix because `client.amc_client.request.call_count` was `2` after message-row pager markup triggered an extra inbox/sentbox page fetch.
- GREEN: `uv run pytest tests/unit/test_private_message.py::TestPrivateMessageCollection::test_acquire_ignores_message_row_pager_markup -q`
- `uv run pytest tests/unit/test_private_message.py::TestPrivateMessageCollection::test_acquire_ignores_non_numeric_pager_targets tests/unit/test_private_message.py::TestPrivateMessageCollection::test_acquire_ignores_message_row_pager_markup tests/unit/test_private_message.py::TestPrivateMessageCollection::test_acquire_deduplicates_message_ids_preserving_order tests/unit/test_private_message.py::TestPrivateMessageCollection::test_acquire_raises_when_paginated_retry_is_exhausted -q` passed 4 tests.
- `uv run pytest tests/unit/test_private_message.py -q` passed 28 tests.
- `uv run pytest tests/unit/test_private_message.py tests/unit/test_client.py -q` passed 47 tests.
- `uv run pytest tests/unit -q` passed 653 tests.
- `uv run ruff check .`
- `uv run ruff format --check .`
- `uv run mypy .`
- `git diff --check`

Not run: `uv run pyright src tests` because this environment could not find a `pyright` executable on PATH in earlier checks.

## Acceptance Criteria

- `div.pager` markup inside `tr.message` rows is treated as message-list row content only.
- Message-row pager markup cannot queue additional inbox/sentbox page requests.
- Real structural inbox/sentbox pagination still queues additional pages.
- Non-numeric pager target handling remains unchanged.
- Existing first-page retry handling, additional-page retry failure behavior, duplicate message ID preservation, empty input behavior, detail parsing, inbox/sentbox factories, and client private-message accessors remain unchanged.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Private-message list rows are content-adjacent records, while the collection pager is module-level structure. `PrivateMessageCollection._acquire(...)` should use structural module pagination to decide additional page requests and ignore pager-like markup that is part of a message row.

## Local Evidence, Not For Upstream Paste

- Earlier local drafts [037-pr-retry-private-message-fetches.md](037-pr-retry-private-message-fetches.md), [054-pr-deduplicate-private-message-detail-fetches.md](054-pr-deduplicate-private-message-detail-fetches.md), [067-pr-deduplicate-direct-private-message-fetches.md](067-pr-deduplicate-direct-private-message-fetches.md), [073-pr-reuse-private-message-detail-parsing.md](073-pr-reuse-private-message-detail-parsing.md), and [077-pr-skip-empty-private-message-fetch-batches.md](077-pr-skip-empty-private-message-fetch-batches.md) established private-message acquisition as a practical local target.
- Pager drafts [097-pr-ignore-forum-content-pager-markup.md](097-pr-ignore-forum-content-pager-markup.md), [098-pr-ignore-thread-description-pager-markup.md](098-pr-ignore-thread-description-pager-markup.md), [099-pr-ignore-recent-change-comment-pager-markup.md](099-pr-ignore-recent-change-comment-pager-markup.md), and [100-pr-ignore-listpages-field-pager-markup.md](100-pr-ignore-listpages-field-pager-markup.md) established the adjacent pagination failure class: content-adjacent markup can otherwise queue phantom page requests.
- The refreshed complexity scan continues to flag shared parser/pagination loops as audit-worthy paths, and the PM list path still had response-wide pager discovery before this fix.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, and message contents out of upstream discussion.

## Additional Notes

This slice does not change request construction, retry policy, batch sizing, message row ID parsing, duplicate message ID handling, message detail parsing, inbox/sentbox wrappers, or the `PrivateMessage` dataclass. It only narrows pager discovery before additional private-message list page requests are queued.
