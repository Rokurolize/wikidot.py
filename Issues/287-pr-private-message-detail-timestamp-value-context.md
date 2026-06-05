# PR Draft: Report Malformed Private Message Detail Timestamps

## Summary

`PrivateMessageCollection.from_ids(...)` parses the private-message detail header `span.odate` into `PrivateMessage.created_at`. Before this slice, a detail response whose timestamp element was present but carried a malformed `time_*` class such as `time_latest` leaked the shared parser's raw `ValueError`. That exception did not identify the dashboard detail module, message ID, affected field, or observed timestamp value.

This follow-up keeps the shared `odate` parser unchanged and catches malformed private-message detail timestamp values at the detail parser boundary. It raises `NoElementException` with the module, message ID, `field=odate`, and offending class value. Valid detail parsing, missing timestamp diagnostics, sender/recipient parsing, subject/body extraction, duplicate-ID ordering, retry behavior, inbox/sent wrappers, and send behavior remain unchanged.

## Related Issue

Builds on [037-pr-retry-private-message-fetches.md](037-pr-retry-private-message-fetches.md), [054-pr-deduplicate-private-message-detail-fetches.md](054-pr-deduplicate-private-message-detail-fetches.md), [067-pr-deduplicate-direct-private-message-fetches.md](067-pr-deduplicate-direct-private-message-fetches.md), [073-pr-reuse-private-message-detail-parsing.md](073-pr-reuse-private-message-detail-parsing.md), [089-pr-scope-private-message-detail-header.md](089-pr-scope-private-message-detail-header.md), [106-pr-preserve-private-message-body-spacing.md](106-pr-preserve-private-message-body-spacing.md), [119-pr-preserve-private-message-subject-spacing.md](119-pr-preserve-private-message-subject-spacing.md), [178-pr-private-message-list-fetch-failure-context.md](178-pr-private-message-list-fetch-failure-context.md), [184-pr-private-message-detail-fetch-context.md](184-pr-private-message-detail-fetch-context.md), [188-pr-private-message-detail-parse-context.md](188-pr-private-message-detail-parse-context.md), [206-pr-private-message-detail-response-body-context.md](206-pr-private-message-detail-response-body-context.md), [207-pr-private-message-list-response-body-context.md](207-pr-private-message-list-response-body-context.md), [272-pr-private-message-detail-timestamp-context.md](272-pr-private-message-detail-timestamp-context.md), and [273-pr-private-message-detail-subject-body-context.md](273-pr-private-message-detail-subject-body-context.md). Those drafts established private-message detail fetching and parsing as a practical browser-free workflow surface, tightened retry/deduplication behavior, scoped detail metadata to the direct header, preserved message text spacing, and made missing detail fields observable.

No upstream issue was filed from this local workspace.

## Changes

- Convert malformed present private-message detail `span.odate` timestamp values from raw `ValueError` into contextual `NoElementException`.
- Include dashboard detail module, message ID, `field=odate`, and the observed `time_*` class value in the parser error.
- Preserve the existing missing-`span.odate` error path from the earlier timestamp-context slice.
- Preserve successful parsing of valid detail timestamps through the shared `odate` parser.
- Add a focused public `PrivateMessageCollection.from_ids(...)` regression for `class="odate time_latest"`.

## Type Of Change

- Bug fix / diagnostics improvement
- Private-message detail parser hardening
- Test update

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| A private-message detail timestamp element with a malformed present `time_*` value fails at the private-message parser boundary. | `TestPrivateMessageCollection.test_from_ids_malformed_odate_includes_module_message_field_and_value_context` returns detail HTML with `class="odate time_latest"` and expects `NoElementException`. | Leaking `ValueError`, fabricating a timestamp, or returning a `PrivateMessage` rejects this local completion claim. |
| The malformed timestamp error identifies the affected module, message, field, and observed class value. | The focused regression asserts `Message odate value is malformed for module: dashboard/messages/DMViewMessageModule, message: 1, field=odate, value=time_latest`. | Omitting module, message ID, `field=odate`, or the raw class value rejects this local completion claim. |
| Existing missing timestamp diagnostics stay intact. | Focused GREEN included `test_from_ids_missing_odate_includes_module_message_and_field_context`. | Regressing the earlier missing-`odate` `NoElementException` rejects this local completion claim. |
| Valid private-message detail parsing remains unchanged. | Focused GREEN included `test_from_ids_success` and `test_from_ids_preserves_body_text_spacing`; the full private-message suite passed 42 tests. | Regressions in valid detail parsing, sender/recipient parsing, subject/body extraction, retry, deduplication, inbox/sent wrappers, or send behavior reject this local completion claim. |
| Adjacent user parsing remains compatible with the unchanged shared parser. | `uv run --extra test pytest tests/unit/test_private_message.py tests/unit/test_user.py -q` passed 58 tests. | Regressing user parsing or private-message detail user construction rejects this local completion claim. |
| Broad unit and static quality gates remain green in the repo dependency environment. | `uv run --extra test pytest tests/unit/ -q`; `uv run ruff check .`; `uv run ruff format --check .`; `uv run mypy src tests`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject this local completion claim. |

## Testing

Implemented locally in commit `2c5c940 fix(private_message): report malformed detail timestamps`.

- RED: `uv run --extra test pytest tests/unit/test_private_message.py::TestPrivateMessageCollection::test_from_ids_malformed_odate_includes_module_message_field_and_value_context -q` failed before the fix with `ValueError: invalid literal for int() with base 10: 'latest'`.
- GREEN: `uv run --extra test pytest tests/unit/test_private_message.py::TestPrivateMessageCollection::test_from_ids_malformed_odate_includes_module_message_field_and_value_context tests/unit/test_private_message.py::TestPrivateMessageCollection::test_from_ids_missing_odate_includes_module_message_and_field_context tests/unit/test_private_message.py::TestPrivateMessageCollection::test_from_ids_success tests/unit/test_private_message.py::TestPrivateMessageCollection::test_from_ids_preserves_body_text_spacing -q` passed 4 tests.
- `uv run --extra test pytest tests/unit/test_private_message.py -q` passed 42 tests.
- `uv run --extra test pytest tests/unit/test_private_message.py tests/unit/test_user.py -q` passed 58 tests.
- `uv run --extra test pytest tests/unit/ -q` passed 844 tests.
- `uv run ruff check .`.
- `uv run ruff format --check .`.
- `uv run mypy src tests`.
- `git diff --check`.

Not run successfully: `command -v pyright` did not find a `pyright` executable.

## Acceptance Criteria

- `PrivateMessageCollection.from_ids(...)` raises `NoElementException` when a private-message detail response has a direct header `span.odate` element whose `time_*` class cannot be parsed as a Unix timestamp.
- The malformed timestamp error includes the dashboard detail module name, message ID, `field=odate`, and observed `time_*` class value.
- Missing `span.odate` detail timestamps continue to raise the existing contextual `NoElementException`.
- Valid detail timestamps still parse through `odate_parser(...)`.
- Subject, body, sender, recipient, duplicate-ID reuse, ordering, retry behavior, inbox/sent wrappers, and send action behavior remain unchanged.
- No private message body, subject text, live Wikidot action, upstream Issue, upstream PR, or push is required for this local draft.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and the local implementation commit.
- The thread HTML report and complexity memo are refreshed after the docs commit.
- Secret and local-path leak checks over the new draft pass before finalizing the turn.

## Upstream-Safe Motivation

Private-message detail timestamps are part of the parsed `PrivateMessage` object and are used by browser-free message collection scripts to build chronological ledgers. A present but malformed timestamp class is a parser contract failure. Reporting the module, message, field, and observed value makes generated-module drift actionable while keeping the generic shared `odate` parser behavior stable for other callers.

## Local Evidence, Not For Upstream Paste

- Earlier private-message drafts improved retry behavior, duplicate detail fetching, direct detail parsing reuse, header scoping, text spacing, response-body context, and missing detail-field diagnostics. This slice targets the remaining malformed-present timestamp value path.
- This slice intentionally targets only private-message detail `span.odate` values that are present but not parseable as Unix timestamps. It does not change message list acquisition, message ID parsing, subject/body extraction, sender/recipient parsing, inbox/sent wrappers, direct send actions, shared `odate` parser behavior, or live Wikidot behavior.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, raw action responses, private message bodies, private message subjects, recipient names from real messages, page source text, page names from real sites, and site contents out of upstream discussion.

## Additional Notes

This is a parser correctness and observability fix. It narrows a raw utility-parser exception into the same local exception family used by the surrounding private-message detail parser.
