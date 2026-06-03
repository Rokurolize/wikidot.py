# PR Draft: Deduplicate Direct Private Message Fetch IDs

## Summary

`PrivateMessageCollection.from_ids(...)`, `PrivateMessageInbox.from_ids(...)`, `PrivateMessageSentBox.from_ids(...)`, and `PrivateMessage.from_id(...)` provide direct private-message detail lookup by message ID. The inbox/sent-box list acquisition path already deduplicates repeated list rows before calling `from_ids(...)`, but callers can still pass duplicate IDs directly, which previously sent duplicate `dashboard/messages/DMViewMessageModule` requests.

This fix groups direct `from_ids(...)` input IDs by first-seen message ID before building AMC request bodies, then rebuilds the returned collection in the caller-requested order. Duplicate positions remain present, each duplicate result position receives a distinct `PrivateMessage` instance, and existing retry, no-message permission mapping, parsing, and send behavior are preserved.

## Related Issue

Builds on the retry-aware private-message read work in [037-pr-retry-private-message-fetches.md](037-pr-retry-private-message-fetches.md) and complements [054-pr-deduplicate-private-message-detail-fetches.md](054-pr-deduplicate-private-message-detail-fetches.md), which deduplicates message IDs discovered while parsing inbox/sent-box list pages before detail acquisition.

No upstream issue was filed from this local workspace.

## Changes

- Track first-seen direct `message_ids` inside `PrivateMessageCollection.from_ids(...)`.
- Send one `dashboard/messages/DMViewMessageModule` request per unique message ID.
- Preserve the caller-requested output length and order for duplicate IDs.
- Build a distinct `PrivateMessage` instance for every returned duplicate position, avoiding shared mutable result objects.
- Preserve `ForbiddenException` mapping for `no_message`, exhausted retry `UnexpectedException`, sender/recipient parsing errors, date parsing, inbox/sent-box wrappers, `PrivateMessage.from_id(...)`, and `PrivateMessage.send(...)`.
- Add a focused public-interface regression test for duplicate direct `from_ids(...)` inputs.

## Type Of Change

- Performance and reliability improvement
- Test-covered behavior fix

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| Avoid duplicate detail fetches for repeated direct private-message IDs. | `TestPrivateMessageCollection.test_from_ids_deduplicates_duplicate_message_ids_preserving_order` asserts AMC request bodies contain `[1, 2]` when the public input is `[1, 1, 2]`. | Reverting the direct-ID grouping makes the RED test fail because request bodies contain `[1, 1, 2]`. |
| Preserve caller-requested collection shape and order. | The focused test asserts returned IDs remain `[1, 1, 2]` and subjects remain `["First Subject", "First Subject", "Second Subject"]`. | Collapsing the public collection would return only two messages and fail the focused test. |
| Preserve distinct result objects for duplicate positions. | The focused test asserts `result[0] is not result[1]`. | Reusing one parsed object for duplicate output positions would create shared mutable result entries and fail the focused test. |
| Preserve existing private-message behavior. | `uv run --extra test pytest tests/unit/test_private_message.py -q`; `uv run --extra test pytest tests/unit/test_private_message.py tests/unit/test_client.py -q`; `uv run --extra test pytest tests/unit -q`. | Regression would break private-message parsing, retry handling, client private-message accessors, direct `from_id`, or broad unit tests. |
| Preserve static quality gates. | `uv run ruff check .`; `uv run ruff format --check .`; `uv run mypy src tests`; `git diff --check`. | Formatting, lint, type, or whitespace failures reject the local completion claim. |

## Testing

Implemented locally in commit `53dc7dd perf(private_message): deduplicate direct message ids`.

- RED: `uv run --extra test pytest tests/unit/test_private_message.py::TestPrivateMessageCollection::test_from_ids_deduplicates_duplicate_message_ids_preserving_order -q` failed before the fix because AMC request bodies contained duplicate IDs `[1, 1, 2]` instead of `[1, 2]`.
- GREEN: `uv run --extra test pytest tests/unit/test_private_message.py::TestPrivateMessageCollection::test_from_ids_deduplicates_duplicate_message_ids_preserving_order -q`
- `uv run --extra test pytest tests/unit/test_private_message.py -q` passed 25 tests.
- `uv run --extra test pytest tests/unit/test_private_message.py tests/unit/test_client.py -q` passed 44 tests.
- `uv run --extra test pytest tests/unit -q` passed 622 tests.
- `uv run ruff check src/wikidot/module/private_message.py tests/unit/test_private_message.py`
- `uv run ruff check .`
- `uv run ruff format --check .`
- `uv run mypy src tests`
- `git diff --check`
- `python3 /home/roku/.codex/skills/complexity-optimizer/scripts/analyze_complexity.py /home/roku/codex-thread-workspaces/019e8a3a-20fd-7113-975d-8c92336695cd/worktrees/wikidot.py --format markdown` refreshed current complexity leads.

## Acceptance Criteria

- Duplicate IDs passed directly to `PrivateMessageCollection.from_ids(...)` send one detail request per unique first-seen ID.
- Returned collection length and order match the caller's original `message_ids` input.
- Duplicate result positions receive distinct `PrivateMessage` instances populated from the shared successful response.
- `PrivateMessageInbox.from_ids(...)`, `PrivateMessageSentBox.from_ids(...)`, and `PrivateMessage.from_id(...)` continue delegating through the same public detail acquisition path.
- `no_message` responses still map to `ForbiddenException` naming the affected message ID.
- Exhausted retry results still raise `UnexpectedException("Cannot retrieve private message: ...")`.
- Missing sender/recipient markup still raises the existing `NoElementException` with the affected message ID.
- `PrivateMessage.send(...)` remains unchanged on the direct send action path.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Direct private-message detail acquisition should avoid redundant dashboard reads when callers pass repeated IDs from merged queues, retry ledgers, or manually combined inbox/sent-box references. Ordered request deduplication reduces AMC traffic without changing the public collection shape expected by callers.

## Local Evidence, Not For Upstream Paste

- Local retry hardening in [037-pr-retry-private-message-fetches.md](037-pr-retry-private-message-fetches.md) established private-message detail acquisition as an active read-heavy surface.
- Local list-row deduplication in [054-pr-deduplicate-private-message-detail-fetches.md](054-pr-deduplicate-private-message-detail-fetches.md) removed duplicate detail requests from inbox/sent-box acquisition but left direct `from_ids(...)` duplicate inputs as a separate public API surface.
- The same duplicate-request pattern was previously found and fixed in forum post sources, forum post revisions, forum post revision HTML, thread post/detail acquisition, page revision source/HTML fetching, page source/revision/file/vote acquisition, and page-ID lookup preflight.
- Keep local rollout paths, account names, private-message bodies, and corpus-specific identifiers out of any upstream discussion.

## Additional Notes

This slice does not change inbox/sent-box list parsing, pagination request construction, retry policy, no-message permission mapping, message HTML parsing, date parsing, client accessor names, or send behavior. It only removes duplicate direct detail requests from the public `from_ids(...)` path while preserving the requested output shape. Follow-up [073-pr-reuse-private-message-detail-parsing.md](073-pr-reuse-private-message-detail-parsing.md) reuses parsed fields for duplicate output positions after this request-level deduplication, and [077-pr-skip-empty-private-message-fetch-batches.md](077-pr-skip-empty-private-message-fetch-batches.md) skips the same direct detail path when the requested ID list is empty.
