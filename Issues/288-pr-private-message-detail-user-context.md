# PR Draft: Report Malformed Private Message Detail Users

## Summary

`PrivateMessageCollection.from_ids(...)` parses the private-message detail header's direct `span.printuser` elements into `PrivateMessage.sender` and `PrivateMessage.recipient`. Before this slice, a detail response whose sender or recipient element existed but carried malformed `userInfo(...)` metadata, such as `userInfo(latest)`, leaked the shared `user_parse(...)` utility's raw `ValueError("user id is not found")`. That exception did not identify the dashboard detail module, message ID, affected user field, or observed `onclick` value.

This follow-up keeps the shared `user_parse(...)` utility unchanged and catches malformed private-message detail sender/recipient values at the detail parser boundary. It raises `NoElementException` with the module, message ID, `field=sender` or `field=recipient`, and the offending direct `onclick` value. Valid sender/recipient parsing, missing sender/recipient-count diagnostics, timestamp diagnostics, subject/body extraction, duplicate-ID ordering, retry behavior, inbox/sent wrappers, and send behavior remain unchanged.

## Related Issue

Builds on [037-pr-retry-private-message-fetches.md](037-pr-retry-private-message-fetches.md), [054-pr-deduplicate-private-message-detail-fetches.md](054-pr-deduplicate-private-message-detail-fetches.md), [067-pr-deduplicate-direct-private-message-fetches.md](067-pr-deduplicate-direct-private-message-fetches.md), [073-pr-reuse-private-message-detail-parsing.md](073-pr-reuse-private-message-detail-parsing.md), [089-pr-scope-private-message-detail-header.md](089-pr-scope-private-message-detail-header.md), [106-pr-preserve-private-message-body-spacing.md](106-pr-preserve-private-message-body-spacing.md), [119-pr-preserve-private-message-subject-spacing.md](119-pr-preserve-private-message-subject-spacing.md), [178-pr-private-message-list-fetch-failure-context.md](178-pr-private-message-list-fetch-failure-context.md), [184-pr-private-message-detail-fetch-context.md](184-pr-private-message-detail-fetch-context.md), [188-pr-private-message-detail-parse-context.md](188-pr-private-message-detail-parse-context.md), [206-pr-private-message-detail-response-body-context.md](206-pr-private-message-detail-response-body-context.md), [207-pr-private-message-list-response-body-context.md](207-pr-private-message-list-response-body-context.md), [272-pr-private-message-detail-timestamp-context.md](272-pr-private-message-detail-timestamp-context.md), [273-pr-private-message-detail-subject-body-context.md](273-pr-private-message-detail-subject-body-context.md), and [287-pr-private-message-detail-timestamp-value-context.md](287-pr-private-message-detail-timestamp-value-context.md). It also follows the same parser-boundary pattern as [285-pr-forum-post-revision-user-context.md](285-pr-forum-post-revision-user-context.md), which converted malformed forum revision `printuser` metadata from raw helper exceptions into contextual parser failures.

No upstream issue was filed from this local workspace.

## Changes

- Convert malformed present private-message detail sender/recipient `printuser` metadata from raw `ValueError` into contextual `NoElementException`.
- Include dashboard detail module, message ID, user field name, and the observed direct `onclick` value in the parser error.
- Preserve the shared `user_parse(...)` utility behavior and parser tests.
- Preserve the existing missing sender/recipient-count error path from the earlier detail parse-context slice.
- Preserve successful parsing of valid private-message detail sender and recipient users.
- Add a focused public `PrivateMessageCollection.from_ids(...)` regression for a malformed recipient `userInfo(latest)` value.

## Type Of Change

- Bug fix / diagnostics improvement
- Private-message detail parser hardening
- Test update

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| A private-message detail recipient element with malformed present `userInfo(...)` metadata fails at the private-message parser boundary. | `TestPrivateMessageCollection.test_from_ids_malformed_recipient_user_includes_module_message_field_and_value_context` returns detail HTML with `userInfo(latest)` and expects `NoElementException`. | Leaking `ValueError`, fabricating a user, or returning a `PrivateMessage` rejects this local completion claim. |
| The malformed user error identifies the affected module, message, field, and observed `onclick` value. | The focused regression asserts `Message recipient user is malformed for module: dashboard/messages/DMViewMessageModule, message: 1, field=recipient, value=WIKIDOT.page.listeners.userInfo(latest); return false;`. | Omitting module, message ID, `field=recipient`, or the raw `onclick` value rejects this local completion claim. |
| Sender and recipient parsing use the same private-message parser-boundary wrapper. | Source inspection of `src/wikidot/module/private_message.py` shows `_parse_message_user(...)` wraps both the sender and recipient `user_parser(...)` calls with the same context format and field-specific names. | Wrapping only the focused recipient path while leaving sender raw would reject this local completion claim. |
| Existing missing sender/recipient-count diagnostics stay intact. | Focused GREEN included `test_from_ids_missing_sender_or_recipient_raises`. | Regressing the earlier missing sender/recipient `NoElementException` rejects this local completion claim. |
| Existing timestamp and successful detail parsing stay intact. | Focused GREEN included malformed timestamp, success, and subject-spacing tests; the full private-message suite passed 43 tests. | Regressions in valid detail parsing, timestamp parsing, subject/body extraction, retry, deduplication, inbox/sent wrappers, or send behavior reject this local completion claim. |
| Shared user parsing and adjacent user workflows remain compatible. | `uv run --extra test pytest tests/unit/test_private_message.py tests/unit/test_user.py tests/unit/parsers/test_user_parser.py -q` passed 74 tests. | Regressing shared user parser behavior or adjacent user models rejects this local completion claim. |
| Broad unit and static quality gates remain green in the repo dependency environment. | `uv run --extra test pytest tests/unit/ -q`; `uv run ruff check .`; `uv run ruff format --check .`; `uv run mypy src tests`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject this local completion claim. |

## Testing

Implemented locally in commit `949892f fix(private_message): report malformed detail users`.

- RED: `uv run --extra test pytest tests/unit/test_private_message.py::TestPrivateMessageCollection::test_from_ids_malformed_recipient_user_includes_module_message_field_and_value_context -q` failed before the fix with `ValueError: user id is not found`.
- GREEN: `uv run --extra test pytest tests/unit/test_private_message.py::TestPrivateMessageCollection::test_from_ids_malformed_recipient_user_includes_module_message_field_and_value_context tests/unit/test_private_message.py::TestPrivateMessageCollection::test_from_ids_missing_sender_or_recipient_raises tests/unit/test_private_message.py::TestPrivateMessageCollection::test_from_ids_malformed_odate_includes_module_message_field_and_value_context tests/unit/test_private_message.py::TestPrivateMessageCollection::test_from_ids_success tests/unit/test_private_message.py::TestPrivateMessageCollection::test_from_ids_preserves_subject_text_spacing -q` passed 5 tests.
- `uv run --extra test pytest tests/unit/test_private_message.py -q` passed 43 tests.
- `uv run --extra test pytest tests/unit/test_private_message.py tests/unit/test_user.py tests/unit/parsers/test_user_parser.py -q` passed 74 tests.
- `uv run --extra test pytest tests/unit/ -q` passed 845 tests.
- `uv run ruff check .`.
- `uv run ruff format --check .`.
- `uv run mypy src tests`.
- `git diff --check`.

Not run successfully: `command -v pyright` did not find a `pyright` executable.

## Acceptance Criteria

- `PrivateMessageCollection.from_ids(...)` raises `NoElementException` when a private-message detail response has a direct header sender or recipient `span.printuser` element whose `userInfo(...)` metadata cannot be parsed by the shared user parser.
- The malformed user error includes the dashboard detail module name, message ID, `field=sender` or `field=recipient`, and observed direct `onclick` value.
- Missing or extra direct sender/recipient elements continue to raise the existing contextual `NoElementException`.
- Valid sender and recipient users still parse through `user_parser(...)`.
- Subject, body, timestamp, duplicate-ID reuse, ordering, retry behavior, inbox/sent wrappers, and send action behavior remain unchanged.
- No private message body, subject text, live Wikidot action, upstream Issue, upstream PR, or push is required for this local draft.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and the local implementation commit.
- The thread HTML report and complexity memo are refreshed after the docs commit.
- Secret and local-path leak checks over the new draft pass before finalizing the turn.

## Upstream-Safe Motivation

Private-message detail sender and recipient users are core routing fields for browser-free message collection. If Wikidot's generated detail module emits malformed direct user metadata, wikidot.py should produce a structured parser failure naming the module, message, field, and observed value instead of forcing callers to infer context from a raw helper exception. That makes message-audit logs actionable without retaining raw private-message HTML, bodies, subjects, account details, or credentials.

## Local Evidence, Not For Upstream Paste

- Earlier private-message drafts improved retry behavior, duplicate detail fetching, direct detail parsing reuse, header scoping, text spacing, response-body context, missing detail-field diagnostics, and malformed timestamp value diagnostics. This slice targets the remaining malformed-present sender/recipient user value path.
- This slice intentionally targets only private-message detail sender/recipient `span.printuser` values that are present but not parseable by the shared user parser. It does not change message list acquisition, message ID parsing, subject/body extraction, timestamp parsing, inbox/sent wrappers, direct send actions, shared `user_parse(...)` behavior, or live Wikidot behavior.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, raw action responses, private message bodies, private message subjects, recipient names from real messages, page source text, page names from real sites, and site contents out of upstream discussion.

## Additional Notes

This is a parser correctness and observability fix. It narrows a raw utility-parser exception into the same local exception family used by the surrounding private-message detail parser.
