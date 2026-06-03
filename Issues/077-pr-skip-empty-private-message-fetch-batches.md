# PR Draft: Skip Empty Private Message Fetch Batches

## Summary

`PrivateMessageCollection.from_ids([])` previously could not treat an empty requested message ID list as a no-op because the `login_required` decorator called `client.login_check()` before the method body could inspect the input. That meant an empty private-message detail lookup still required login even though it would not read any message, build any `dashboard/messages/DMViewMessageModule` body, or call AMC.

This fix returns an empty `PrivateMessageCollection` immediately when the requested message ID list is empty. Non-empty direct private-message lookup still calls `client.login_check()` before request deduplication and detail acquisition, and existing retry behavior, `no_message` permission mapping, per-message parsing, duplicate-output handling, inbox/sent-box wrappers, and send behavior remain unchanged.

## Related Issue

Builds on [037-pr-retry-private-message-fetches.md](037-pr-retry-private-message-fetches.md), which made private-message detail reads retry-aware, [054-pr-deduplicate-private-message-detail-fetches.md](054-pr-deduplicate-private-message-detail-fetches.md), which deduplicates message IDs discovered from inbox/sent-box rows, [067-pr-deduplicate-direct-private-message-fetches.md](067-pr-deduplicate-direct-private-message-fetches.md), which deduplicates direct message ID inputs, and [073-pr-reuse-private-message-detail-parsing.md](073-pr-reuse-private-message-detail-parsing.md), which reuses parsed detail fields for duplicate direct outputs. It also mirrors the empty direct thread lookup pattern in [076-pr-skip-empty-thread-fetch-batches.md](076-pr-skip-empty-thread-fetch-batches.md).

No upstream issue was filed from this local workspace.

## Changes

- Return `PrivateMessageCollection([])` immediately from `PrivateMessageCollection.from_ids(...)` when `message_ids` is empty.
- Move login enforcement from the decorator to an explicit `client.login_check()` call after the empty-input guard.
- Preserve non-empty direct request construction, first-seen duplicate-ID request deduplication, retry-aware AMC, `no_message` to `ForbiddenException` mapping, exhausted retry errors, sender/recipient/date parsing, duplicate output ordering, `PrivateMessageInbox.from_ids(...)`, `PrivateMessageSentBox.from_ids(...)`, `PrivateMessage.from_id(...)`, and `PrivateMessage.send(...)`.
- Add a focused public-interface regression test proving empty direct private-message lookup does not call login or AMC.

## Type Of Change

- Performance improvement
- Ergonomics improvement
- Test addition/modification

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| Empty direct private-message lookup should not require login. | `TestPrivateMessageCollection.test_from_ids_empty_input_skips_login_and_fetch` sets `login_check` to raise and asserts `PrivateMessageCollection.from_ids(mock_client, [])` returns an empty collection. | The RED test failed before the fix because the decorator called `client.login_check()` and raised `LoginRequiredException`. |
| Empty direct private-message lookup should not issue an empty AMC batch. | The focused test asserts `mock_client.amc_client.request.assert_not_called()`. | An empty request body sent to AMC would fail the focused test. |
| Empty direct private-message lookup should return the expected collection type. | The focused test asserts the result is a `PrivateMessageCollection` and has length `0`. | Returning a plain list or `None` would fail the focused test. |
| Non-empty direct private-message lookup should still require login. | Existing `TestPrivateMessageCollection.test_from_ids_requires_login` passes for `[1, 2, 3]`. | Moving the login check incorrectly or dropping it would fail the existing non-empty login test. |
| Existing private-message behavior stays green. | `uv run --extra test pytest tests/unit/test_private_message.py -q` passed 26 tests; `uv run --extra test pytest tests/unit/test_private_message.py tests/unit/test_client.py -q` passed 45 tests. | Regressions in retry, parsing, wrapper accessors, direct `from_id`, or client private-message helpers reject the local completion claim. |
| Existing unit behavior stays green. | `uv run --extra test pytest tests/unit -q` passed 630 tests. | Any broad unit regression rejects the local completion claim. |
| Static quality gates remain green. | `uv run ruff check .`; `uv run ruff format --check .`; `uv run mypy src tests`; `git diff --check`. | Formatting, lint, type, or whitespace failures reject the local completion claim. |
| Complexity evidence is interpreted conservatively. | The refreshed scanner artifact remains a lead list; the claimed improvement is empty-batch elimination on direct private-message lookup, not removal of all private-message complexity warnings. | Overclaiming that private-message scanner warnings disappeared would reject the draft. |

## Testing

Implemented locally in commit `b891a74 perf(private_message): skip empty message fetch batches`.

- RED: `uv run --extra test pytest tests/unit/test_private_message.py::TestPrivateMessageCollection::test_from_ids_empty_input_skips_login_and_fetch -q` failed before the fix because `client.login_check()` ran through the decorator before empty input could return.
- GREEN: `uv run --extra test pytest tests/unit/test_private_message.py::TestPrivateMessageCollection::test_from_ids_empty_input_skips_login_and_fetch -q`
- `uv run --extra test pytest tests/unit/test_private_message.py -q` passed 26 tests.
- `uv run --extra test pytest tests/unit/test_private_message.py tests/unit/test_client.py -q` passed 45 tests.
- `uv run --extra test pytest tests/unit -q` passed 630 tests.
- `uv run ruff check src/wikidot/module/private_message.py tests/unit/test_private_message.py`
- `uv run ruff format --check src/wikidot/module/private_message.py tests/unit/test_private_message.py`
- `uv run mypy src/wikidot/module/private_message.py tests/unit/test_private_message.py`
- `uv run ruff check .`
- `uv run ruff format --check .`
- `uv run mypy src tests`
- `git diff --check`

Not run: `uv run pyright src tests` because this environment could not spawn the `pyright` executable.

## Acceptance Criteria

- `PrivateMessageCollection.from_ids(client, [])` returns an empty `PrivateMessageCollection`.
- Empty input does not call `client.login_check()`.
- Empty input does not call `client.amc_client.request(...)`.
- `PrivateMessageInbox.from_ids(client, [])` and `PrivateMessageSentBox.from_ids(client, [])` continue wrapping the shared empty base collection path through `_factory_from_ids(...)`.
- Non-empty `PrivateMessageCollection.from_ids(...)` still calls `client.login_check()` before building or sending private-message detail requests.
- Duplicate non-empty message IDs are still fetched once and returned in caller-requested order.
- Duplicate non-empty output positions still receive distinct `PrivateMessage` instances populated from reused parsed fields.
- `no_message` responses still map to `ForbiddenException` naming the affected message ID.
- Exhausted retry results still raise `UnexpectedException("Cannot retrieve private message: ...")`.
- Missing sender/recipient markup still raises the existing `NoElementException` with the affected message ID.
- `PrivateMessage.send(...)` remains unchanged on the direct send action path.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Direct private-message lookup is useful in scripts that merge inbox/sent-box references, replay queue state, or conditionally inspect message IDs after filtering and permission pruning. Empty ID lists naturally arise from those workflows. Treating empty input as a typed no-op avoids an unnecessary login precondition and avoids empty AMC traffic while preserving all protected behavior for non-empty private-message reads.

## Local Evidence, Not For Upstream Paste

- Local private-message read hardening in [037-pr-retry-private-message-fetches.md](037-pr-retry-private-message-fetches.md), [054-pr-deduplicate-private-message-detail-fetches.md](054-pr-deduplicate-private-message-detail-fetches.md), [067-pr-deduplicate-direct-private-message-fetches.md](067-pr-deduplicate-direct-private-message-fetches.md), and [073-pr-reuse-private-message-detail-parsing.md](073-pr-reuse-private-message-detail-parsing.md) established private-message detail lookup as an active read-heavy surface.
- The focused RED test demonstrated the previous empty-input behavior through the public `PrivateMessageCollection.from_ids(...)` API.
- The same empty-batch pattern was fixed for direct thread lookup in [076-pr-skip-empty-thread-fetch-batches.md](076-pr-skip-empty-thread-fetch-batches.md).
- Keep local rollout paths, account names, private-message bodies, and corpus-specific identifiers out of any upstream discussion.

## Additional Notes

This slice does not change inbox/sent-box list retrieval, pagination request construction, non-empty direct private-message detail lookup, duplicate message ID request deduplication, duplicate parse reuse, retry policy, no-message permission mapping, message field selectors, date parsing semantics, client accessor names, or send behavior. It only skips the direct private-message detail request path when there are no requested message IDs.
