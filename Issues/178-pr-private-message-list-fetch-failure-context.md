# PR Draft: Include Module Context In Private Message List Fetch Failures

## Summary

`PrivateMessageCollection._acquire(client, module_name)` powers both inbox and sent-box private-message list reads. When retry-aware list-page fetching was exhausted, it raised `UnexpectedException("Cannot retrieve private messages page: ...")`, which identified the failed page but not whether the failing list was inbox or sent messages.

This follow-up preserves retry-aware first-page and paginated list fetching, first-page body reuse, non-numeric pager handling, message-row pager filtering, nested-row rejection, duplicate message-ID deduplication, detail fetch behavior, and no-partial-success behavior for failed list pages, but includes the requested dashboard module name and page number in exhausted private-message list fetch failures.

## Related Issue

Builds on [037-pr-retry-private-message-fetches.md](037-pr-retry-private-message-fetches.md), [054-pr-deduplicate-private-message-detail-fetches.md](054-pr-deduplicate-private-message-detail-fetches.md), [073-pr-reuse-private-message-detail-parsing.md](073-pr-reuse-private-message-detail-parsing.md), [101-pr-ignore-private-message-row-pager-markup.md](101-pr-ignore-private-message-row-pager-markup.md), [102-pr-ignore-private-message-nested-row-markup.md](102-pr-ignore-private-message-nested-row-markup.md), [106-pr-preserve-private-message-body-spacing.md](106-pr-preserve-private-message-body-spacing.md), [119-pr-preserve-private-message-subject-spacing.md](119-pr-preserve-private-message-subject-spacing.md), and [163-pr-private-message-list-row-error-context.md](163-pr-private-message-list-row-error-context.md), because those drafts established retry-aware PM reads, stable list parsing, duplicate/detail behavior, text preservation, and module/page/row parser diagnostics.

No upstream issue was filed from this local workspace.

## Changes

- Include the requested private-message dashboard module name and page number when the first list page retry is exhausted.
- Include the same module/page context when a paginated list-page retry is exhausted.
- Add a first-page exhausted retry regression and tighten the existing paginated exhausted retry regression.
- Preserve inbox/sent wrappers, retry policy, first-page body reuse, pager filtering, nested-row rejection, duplicate message-ID deduplication, detail fetching, and no-partial-success behavior.

## Type Of Change

- Bug fix / diagnostics improvement
- Private message list fetch failure context
- Test addition

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| Exhausted first-page private-message list fetches still fail. | `TestPrivateMessageCollection.test_acquire_raises_when_first_page_retry_is_exhausted` returns retry failures, expects `UnexpectedException`, and asserts `from_ids(...)` is not called. | Returning an empty message list, falling through to parsing, or fetching message details after list failure rejects this local completion claim. |
| First-page list failures identify the module and page. | The focused first-page regression asserts `Cannot retrieve private messages for module: dashboard/messages/DMInboxModule, page: 1`. | The RED test failed before the fix because the message only named page `1`. |
| Paginated list failures identify the module and page. | `TestPrivateMessageCollection.test_acquire_raises_when_paginated_retry_is_exhausted` asserts `Cannot retrieve private messages for module: dashboard/messages/DMInboxModule, page: 2`. | The RED test failed before the fix because the message only named page `2`. |
| Private message behavior remains green. | `uv run pytest tests/unit/test_private_message.py -q` passed 33 tests. | Regressions in detail fetches, forbidden handling, inbox/sent wrappers, pager handling, nested-row rejection, duplicate ID handling, text spacing, or send/from-id behavior reject this local completion claim. |
| Broad unit and static quality gates remain green. | `uv run pytest tests/unit -q`; `uv run ruff check src tests`; `uv run ruff format --check src tests`; `uv run mypy src tests`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject this local completion claim. |

## Testing

Implemented locally in commit `c95d5a1 fix(private_message): include module in list fetch failures`.

- RED: `uv run pytest tests/unit/test_private_message.py::TestPrivateMessageCollection::test_acquire_raises_when_first_page_retry_is_exhausted tests/unit/test_private_message.py::TestPrivateMessageCollection::test_acquire_raises_when_paginated_retry_is_exhausted -q` failed before the fix because both messages only named the failed page number.
- GREEN: `uv run pytest tests/unit/test_private_message.py::TestPrivateMessageCollection::test_acquire_raises_when_first_page_retry_is_exhausted tests/unit/test_private_message.py::TestPrivateMessageCollection::test_acquire_raises_when_paginated_retry_is_exhausted -q`
- `uv run pytest tests/unit/test_private_message.py -q` passed 33 tests.
- `uv run pytest tests/unit -q` passed 725 tests.
- `uv run ruff check src tests`
- `uv run ruff format --check src tests`
- `uv run mypy src tests`
- `git diff --check`

Not run successfully: `pyright` because this environment could not find a `pyright` executable.

## Acceptance Criteria

- Retry-exhausted private-message list fetches still raise `UnexpectedException` on the first page and paginated pages.
- Those exceptions include the requested module name and failed page number.
- Inbox and sent-box wrappers, list parsing, pager handling, duplicate message-ID handling, detail fetches, and no-partial-success behavior remain unchanged.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Private-message list fetches share one helper for inbox and sent messages. When a multi-step run exhausts retry for a list page, the caller should know which dashboard module failed without storing raw PM list HTML, message bodies, credentials, or local rollout details.

## Local Evidence, Not For Upstream Paste

- Earlier local drafts established private-message list fetching, detail fetching, duplicate handling, pager filtering, nested-row rejection, and text preservation as practical local Codex surfaces.
- Recent fetch-context slices showed that compact object/module identifiers improve multi-surface ledgers without changing successful behavior.
- The refreshed complexity memo continues to keep parser/source collection helpers, action/read boundaries, and direct property/parser failure messages as follow-up leads, but this slice only claims private-message list fetch diagnostics.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, raw PM list HTML, message bodies, message subjects, and private user data out of upstream discussion.

## Additional Notes

This slice intentionally does not change request module names, retry policy, inbox/sent wrappers, pager parsing, message-row parsing, duplicate message-ID deduplication, detail fetches, send behavior, or live Wikidot behavior. It only adds module/page context to existing exhausted private-message list fetch failures.
