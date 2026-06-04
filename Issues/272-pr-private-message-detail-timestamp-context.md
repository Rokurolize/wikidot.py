# PR Draft: Require Private Message Detail Timestamps

## Summary

`PrivateMessageCollection.from_ids(...)` parses private-message detail HTML into `PrivateMessage.created_at`. Before this slice, a malformed detail response that omitted the header `<span class="odate">` was accepted as a successful parse and silently converted to `datetime.fromtimestamp(0)`. That made browser-free message audit ledgers look like a real 1970 timestamp instead of surfacing the Wikidot detail-parser failure.

This follow-up treats a missing private-message detail timestamp as malformed input. It raises `NoElementException` with the dashboard detail module, message ID, and missing `odate` field before constructing a `PrivateMessage`. Valid detail parsing, sender/recipient parsing, subject/body text spacing, duplicate-ID ordering, retry behavior, inbox/sent wrappers, and `PrivateMessage.send(...)` remain unchanged.

## Related Issue

Builds on [037-pr-retry-private-message-fetches.md](037-pr-retry-private-message-fetches.md), [054-pr-deduplicate-private-message-detail-fetches.md](054-pr-deduplicate-private-message-detail-fetches.md), [067-pr-deduplicate-direct-private-message-fetches.md](067-pr-deduplicate-direct-private-message-fetches.md), [073-pr-reuse-private-message-detail-parsing.md](073-pr-reuse-private-message-detail-parsing.md), [158-pr-private-message-send-action-status-context.md](158-pr-private-message-send-action-status-context.md), and [254-pr-private-message-send-action-status-context.md](254-pr-private-message-send-action-status-context.md). Those drafts established private-message detail fetching, direct detail parsing, and send-action validation as practical browser-free message workflow surfaces.

No upstream issue was filed from this local workspace.

## Changes

- Reject private-message detail responses that omit the direct header `span.odate` timestamp element.
- Include dashboard detail module, message ID, and missing field context in the `NoElementException`.
- Remove the misleading `datetime.fromtimestamp(0)` fallback for malformed detail timestamps.
- Add a focused regression for missing detail timestamp behavior.
- Preserve valid private-message parsing, detail retry, duplicate-ID deduplication, ordering, inbox/sent wrappers, subject/body text spacing, and send behavior.

## Type Of Change

- Bug fix / diagnostics improvement
- Private-message detail parser hardening
- Test addition

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| Missing private-message detail timestamps fail instead of fabricating epoch created-at values. | `TestPrivateMessageCollection.test_from_ids_missing_odate_includes_module_message_and_field_context` returns detail HTML without `span.odate` and asserts `NoElementException`. | Returning a `PrivateMessage` with `created_at == datetime.fromtimestamp(0)` rejects this local completion claim. |
| The malformed-detail error identifies the dashboard detail module, message ID, and missing field. | The focused regression asserts `Message odate element is not found for module: dashboard/messages/DMViewMessageModule, message: 1, field=odate`. | Omitting module, message ID, or field context rejects this local completion claim. |
| Valid private-message detail parsing remains unchanged. | `tests/unit/test_private_message.py` still covers successful `from_ids`, body/header scoping, subject/body spacing, duplicate-ID ordering, retry behavior, inbox/sent acquisition, and send action behavior. | Regressions in valid message detail parsing or collection wrappers reject this local completion claim. |
| Adjacent client private-message accessors remain unchanged. | `uv run --extra test pytest tests/unit/test_private_message.py tests/unit/test_client.py -q` passed 58 tests. | Regressions in `client.private_message` inbox, sentbox, get, or send delegation reject this local completion claim. |
| Broad unit and static quality gates remain green. | `uv run --extra test pytest tests/unit -q`; `uv run ruff check`; `uv run ruff format --check`; `uv run mypy src tests`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject this local completion claim. |

## Testing

Implemented locally in commit `94b69c7 fix(private_message): require detail timestamp`.

- RED: `uv run --extra test pytest tests/unit/test_private_message.py::TestPrivateMessageCollection::test_from_ids_missing_odate_includes_module_message_and_field_context -q` failed before the fix with `Failed: DID NOT RAISE <class 'wikidot.common.exceptions.NoElementException'>`.
- GREEN: `uv run --extra test pytest tests/unit/test_private_message.py::TestPrivateMessageCollection::test_from_ids_missing_odate_includes_module_message_and_field_context -q` passed.
- `uv run --extra test pytest tests/unit/test_private_message.py tests/unit/test_client.py -q` passed 58 tests.
- `uv run --extra test pytest tests/unit -q` passed 829 tests.
- `uv run ruff check`.
- `uv run ruff format --check`.
- `uv run mypy src tests`.
- `git diff --check`.

Not run successfully: `uv run pyright --version` because this environment could not find a `pyright` executable.

## Acceptance Criteria

- `PrivateMessageCollection.from_ids(...)` raises `NoElementException` when a detail response omits `span.odate`.
- The malformed-detail message includes the dashboard detail module name, message ID, and `field=odate`.
- Valid detail parses still produce `PrivateMessage.created_at` through `odate_parser(...)`.
- Subject and body parsing behavior remains unchanged, including empty-text handling when the elements are present but blank.
- No private message body, subject text, live Wikidot action, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Private-message detail timestamps are part of the parsed `PrivateMessage` object. A missing timestamp element is a parser contract failure, not a real message sent at the Unix epoch. Raising a contextual parser exception lets browser-free message collection scripts classify malformed detail pages cleanly and prevents audit ledgers from recording misleading `1970-01-01` message times.

## Local Evidence, Not For Upstream Paste

- Earlier private-message drafts improved retry behavior, duplicate detail fetching, detail parser scoping, and send-action status validation. This slice targets the remaining detail timestamp fallback.
- This slice intentionally targets only missing detail timestamps. It does not change message list acquisition, message ID parsing, subject/body text extraction, sender/recipient parsing, inbox/sent wrappers, direct send actions, or live Wikidot behavior.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, raw action responses, private message bodies, private message subjects, recipient names from real messages, page source text, page names from real sites, and site contents out of upstream discussion.

## Additional Notes

This is a parser correctness and observability fix. It removes a misleading fallback value while preserving successful detail parsing and collection ordering semantics.
