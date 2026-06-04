# PR Draft: Require Private Message Detail Subject And Body Elements

## Summary

`PrivateMessageCollection.from_ids(...)` parses private-message detail HTML into `PrivateMessage.subject` and `PrivateMessage.body`. Before this slice, a malformed detail response that omitted the direct header `span.subject` or direct message `div.body` element was accepted as a successful parse and silently converted the missing field to an empty string. That made browser-free message collection scripts unable to distinguish a genuinely blank subject/body from a broken Wikidot detail page or parser mismatch.

This follow-up treats missing private-message detail subject and body elements as malformed input. It raises `NoElementException` with the dashboard detail module, message ID, and missing field before constructing a `PrivateMessage`. Present-but-empty subject/body elements can still parse as empty text; valid detail parsing, sender/recipient parsing, timestamp parsing, duplicate-ID ordering, retry behavior, inbox/sent wrappers, and `PrivateMessage.send(...)` remain unchanged.

## Related Issue

Builds on [037-pr-retry-private-message-fetches.md](037-pr-retry-private-message-fetches.md), [054-pr-deduplicate-private-message-detail-fetches.md](054-pr-deduplicate-private-message-detail-fetches.md), [067-pr-deduplicate-direct-private-message-fetches.md](067-pr-deduplicate-direct-private-message-fetches.md), [073-pr-reuse-private-message-detail-parsing.md](073-pr-reuse-private-message-detail-parsing.md), [254-pr-private-message-send-action-status-context.md](254-pr-private-message-send-action-status-context.md), and [272-pr-private-message-detail-timestamp-context.md](272-pr-private-message-detail-timestamp-context.md). Those drafts established private-message detail fetching, direct detail parsing, send-action validation, and timestamp parser validation as practical browser-free message workflow surfaces.

No upstream issue was filed from this local workspace.

## Changes

- Reject private-message detail responses that omit the direct header `span.subject` element.
- Reject private-message detail responses that omit the direct message `div.body` element.
- Include dashboard detail module, message ID, and missing field context in both `NoElementException` messages.
- Remove silent absent-element fallback to empty subject/body strings while preserving empty-text parsing for present elements.
- Add focused regressions for missing subject and missing body behavior.
- Preserve valid private-message parsing, detail retry, duplicate-ID deduplication, ordering, inbox/sent wrappers, timestamp parsing, subject/body text spacing, and send behavior.

## Type Of Change

- Bug fix / diagnostics improvement
- Private-message detail parser hardening
- Test addition

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| Missing private-message detail subject elements fail instead of fabricating empty subjects. | `TestPrivateMessageCollection.test_from_ids_missing_subject_includes_module_message_and_field_context` returns detail HTML without `span.subject` and asserts `NoElementException`. | Returning a `PrivateMessage` with `subject == ""` when the element is absent rejects this local completion claim. |
| Missing private-message detail body elements fail instead of fabricating empty bodies. | `TestPrivateMessageCollection.test_from_ids_missing_body_includes_module_message_and_field_context` returns detail HTML without `div.body` and asserts `NoElementException`. | Returning a `PrivateMessage` with `body == ""` when the element is absent rejects this local completion claim. |
| Malformed-detail errors identify dashboard detail module, message ID, and missing field. | The focused regressions assert `field=subject` and `field=body` messages for `dashboard/messages/DMViewMessageModule, message: 1`. | Omitting module, message ID, or field context rejects this local completion claim. |
| Valid private-message detail parsing remains unchanged. | `tests/unit/test_private_message.py` still covers successful `from_ids`, body/header scoping, subject/body spacing, duplicate-ID ordering, retry behavior, timestamp parsing, inbox/sent acquisition, and send action behavior. | Regressions in valid message detail parsing or collection wrappers reject this local completion claim. |
| Adjacent client private-message accessors remain unchanged. | `uv run --extra test pytest tests/unit/test_private_message.py tests/unit/test_client.py -q` passed 60 tests. | Regressions in `client.private_message` inbox, sentbox, get, or send delegation reject this local completion claim. |
| Broad unit and static quality gates remain green. | `uv run --extra test pytest tests/unit -q`; `uv run ruff check`; `uv run ruff format --check`; `uv run mypy src tests`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject this local completion claim. |

## Testing

Implemented locally in commit `7aa038c fix(private_message): require detail subject and body`.

- RED: `uv run --extra test pytest tests/unit/test_private_message.py::TestPrivateMessageCollection::test_from_ids_missing_subject_includes_module_message_and_field_context tests/unit/test_private_message.py::TestPrivateMessageCollection::test_from_ids_missing_body_includes_module_message_and_field_context -q` failed before the fix with two `Failed: DID NOT RAISE <class 'wikidot.common.exceptions.NoElementException'>` failures.
- GREEN: `uv run --extra test pytest tests/unit/test_private_message.py::TestPrivateMessageCollection::test_from_ids_missing_subject_includes_module_message_and_field_context tests/unit/test_private_message.py::TestPrivateMessageCollection::test_from_ids_missing_body_includes_module_message_and_field_context tests/unit/test_private_message.py::TestPrivateMessageCollection::test_from_ids_missing_odate_includes_module_message_and_field_context -q` passed 3 tests.
- `uv run --extra test pytest tests/unit/test_private_message.py tests/unit/test_client.py -q` passed 60 tests.
- `uv run --extra test pytest tests/unit -q` passed 831 tests.
- `uv run ruff check`.
- `uv run ruff format --check`.
- `uv run mypy src tests`.
- `git diff --check`.

Not run successfully: `uv run pyright --version` because this environment could not find a `pyright` executable.

## Acceptance Criteria

- `PrivateMessageCollection.from_ids(...)` raises `NoElementException` when a detail response omits direct `span.subject`.
- `PrivateMessageCollection.from_ids(...)` raises `NoElementException` when a detail response omits direct `div.body`.
- Malformed-detail messages include the dashboard detail module name, message ID, and `field=subject` or `field=body`.
- Valid detail parses still produce `PrivateMessage.subject` and `PrivateMessage.body` from present elements, including blank present elements.
- No private message body, subject text, live Wikidot action, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Private-message subject and body are first-class parsed fields. Missing DOM elements are parser contract failures, not proof that a message has an empty subject or body. Raising contextual parser exceptions lets browser-free message collection scripts classify malformed detail pages cleanly and avoids conflating valid blank text with broken markup.

## Local Evidence, Not For Upstream Paste

- Earlier private-message drafts improved retry behavior, duplicate detail fetching, detail parser scoping, send-action status validation, and missing timestamp handling. This slice targets the remaining absent subject/body fallbacks.
- This slice intentionally targets only absent detail subject/body elements. It does not require non-empty text, change message list acquisition, change message ID parsing, alter timestamp parsing, touch sender/recipient parsing, alter inbox/sent wrappers, touch direct send actions, or modify live Wikidot behavior.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, raw action responses, private message bodies, private message subjects, recipient names from real messages, page source text, page names from real sites, and site contents out of upstream discussion.

## Additional Notes

This is a parser correctness and observability fix. It removes misleading absent-element fallbacks while preserving successful detail parsing and collection ordering semantics.
