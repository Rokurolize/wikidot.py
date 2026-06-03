# PR Draft: Reuse Private Message Detail Parsing For Duplicate IDs

## Summary

`PrivateMessageCollection.from_ids(...)` already deduplicates duplicate direct message IDs before sending `dashboard/messages/DMViewMessageModule` requests, then rebuilds the returned collection in the caller-requested order. The duplicate output positions still reparsed the same successful response body, reran sender/recipient parsing, and reran date parsing for each repeated ID.

This fix parses each unique successful private-message detail response once, stores the parsed sender, recipient, subject, body, and timestamp fields by message ID, then creates a distinct `PrivateMessage` instance for every caller-requested output position. The public collection shape, order, duplicate entries, and error handling remain unchanged.

## Related Issue

Builds directly on [067-pr-deduplicate-direct-private-message-fetches.md](067-pr-deduplicate-direct-private-message-fetches.md), which removed duplicate direct detail requests while preserving duplicate output positions. It also complements [054-pr-deduplicate-private-message-detail-fetches.md](054-pr-deduplicate-private-message-detail-fetches.md), which deduplicates message IDs discovered from inbox/sent-box list pages before detail acquisition.

No upstream issue was filed from this local workspace.

## Changes

- Parse each unique successful direct private-message detail response once inside `PrivateMessageCollection.from_ids(...)`.
- Reuse parsed field values for duplicate caller-requested output positions.
- Preserve distinct `PrivateMessage` instances for duplicate returned positions.
- Preserve first-seen request deduplication, caller-requested result ordering, retry handling, `no_message` permission mapping, missing sender/recipient errors, inbox/sent-box wrappers, `PrivateMessage.from_id(...)`, and send behavior.
- Strengthen the existing duplicate-ID regression test to assert one response JSON parse and one sender/recipient/date parse pair per unique message ID.

## Type Of Change

- Performance improvement
- Refactoring
- Test addition/modification

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| Duplicate direct private-message IDs should not reparse the same detail response body. | `TestPrivateMessageCollection.test_from_ids_deduplicates_duplicate_message_ids_preserving_order` asserts `first_response.json.call_count == 1` for public input `[1, 1, 2]`. | The RED test failed before the fix because the first response JSON body was parsed twice. |
| Duplicate direct private-message IDs should not rerun sender/recipient/date parsing for duplicate output positions. | The focused test asserts `mock_user_parser.call_count == 4` and `mock_odate_parser.call_count == 2` for two unique responses. | The pre-fix path called the user parser six times and the date parser three times for `[1, 1, 2]`. |
| The public collection shape, order, and duplicate entries stay unchanged. | The focused test still asserts returned IDs `[1, 1, 2]` and subjects `["First Subject", "First Subject", "Second Subject"]`. | Collapsing duplicate output positions would fail the focused test. |
| Duplicate result positions remain distinct message objects. | The focused test still asserts `result[0] is not result[1]`. | Reusing a single `PrivateMessage` instance for both positions would fail the focused test. |
| Existing private-message behavior stays green. | `uv run --extra test pytest tests/unit/test_private_message.py -q`; `uv run --extra test pytest tests/unit/test_private_message.py tests/unit/test_client.py -q`; `uv run --extra test pytest tests/unit -q`. | Regressions in retry, parsing, wrapper accessors, or direct `from_id` behavior reject the local completion claim. |
| Static quality gates remain green. | `uv run ruff check .`; `uv run ruff format --check .`; `uv run mypy src tests`; `git diff --check`. | Formatting, lint, type, or whitespace failures reject the local completion claim. |
| Complexity evidence is interpreted conservatively. | The refreshed scanner artifact still flags the remaining per-unique-ID private-message parse loop; the claimed improvement is duplicate-response parse reuse, not removal of all per-message parsing. | Overclaiming that `private_message.py` scanner warnings disappeared would reject the draft. |

## Testing

Implemented locally in commit `f64e72a perf(private_message): reuse parsed duplicate details`.

- RED: `uv run --extra test pytest tests/unit/test_private_message.py::TestPrivateMessageCollection::test_from_ids_deduplicates_duplicate_message_ids_preserving_order -q` failed before the fix with `assert 2 == 1` for `first_response.json.call_count`.
- GREEN: `uv run --extra test pytest tests/unit/test_private_message.py::TestPrivateMessageCollection::test_from_ids_deduplicates_duplicate_message_ids_preserving_order -q`
- `uv run --extra test pytest tests/unit/test_private_message.py -q` passed 25 tests.
- `uv run --extra test pytest tests/unit/test_private_message.py tests/unit/test_client.py -q` passed 44 tests.
- `uv run --extra test pytest tests/unit -q` passed 628 tests.
- `uv run ruff check .`
- `uv run ruff format --check .`
- `uv run mypy src tests`
- `git diff --check`
- `python3 /home/roku/.codex/skills/complexity-optimizer/scripts/analyze_complexity.py /home/roku/codex-thread-workspaces/019e8a3a-20fd-7113-975d-8c92336695cd/worktrees/wikidot.py --format markdown` refreshed current complexity leads.

Not run: `uv run pyright src tests` because this environment could not spawn the `pyright` executable.

## Acceptance Criteria

- Duplicate IDs passed directly to `PrivateMessageCollection.from_ids(...)` still send one detail request per unique first-seen ID.
- Each successful unique detail response body is parsed once.
- Sender/recipient user parsing and date parsing run once per unique detail response, not once per duplicate output position.
- Returned collection length and order match the caller's original `message_ids` input.
- Duplicate result positions receive distinct `PrivateMessage` instances populated from the parsed field values for the shared successful response.
- `PrivateMessageInbox.from_ids(...)`, `PrivateMessageSentBox.from_ids(...)`, and `PrivateMessage.from_id(...)` continue delegating through the same public detail acquisition path.
- `no_message` responses still map to `ForbiddenException` naming the affected message ID.
- Exhausted retry results still raise `UnexpectedException("Cannot retrieve private message: ...")`.
- Missing sender/recipient markup still raises the existing `NoElementException` with the affected message ID.
- `PrivateMessage.send(...)` remains unchanged on the direct send action path.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Direct private-message detail acquisition can receive repeated IDs from merged inbox/sent-box references, queue replay, or caller-side deduplication misses. Once a duplicate ID maps to the same successful response body, reparsing the HTML and reparsing sender/recipient/date metadata does not add information. Reusing parsed fields reduces avoidable CPU work while preserving the public ordered collection and distinct message objects.

## Local Evidence, Not For Upstream Paste

- [067-pr-deduplicate-direct-private-message-fetches.md](067-pr-deduplicate-direct-private-message-fetches.md) removed duplicate direct detail requests but intentionally preserved duplicate result positions.
- The focused RED test demonstrated the remaining cost: duplicate output positions still parsed the same response body twice.
- The refreshed complexity scan continues to flag `src/wikidot/module/private_message.py` around the per-unique-ID detail parse loop and list acquisition loop; this slice addresses duplicate parse fan-out only.
- Keep local rollout paths, account names, private-message bodies, and corpus-specific identifiers out of any upstream discussion.

## Additional Notes

This slice does not change inbox/sent-box list parsing, pagination request construction, retry policy, no-message permission mapping, message field selectors, date parsing semantics, client accessor names, or send behavior. It only avoids redoing the same successful detail parse for duplicate direct `from_ids(...)` output positions.
