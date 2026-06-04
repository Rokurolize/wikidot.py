# PR Draft: Include Module Context In Private Message Detail Parse Errors

## Summary

`PrivateMessageCollection.from_ids(...)` retrieves direct private-message details through `dashboard/messages/DMViewMessageModule` and parses the structural `div.pmessage` detail HTML. Earlier local slices made direct detail reads retry-aware, deduplicated duplicate direct IDs, reused duplicate parsed detail responses, scoped detail-header parsing, and added module/message context to direct detail fetch failures. The remaining malformed detail HTML parser errors still identified only the message ID.

This follow-up keeps login checks, request payloads, retry counts, `no_message` handling, duplicate-ID preservation, successful parsing, subject/body spacing, sender/recipient parsing, and exception types unchanged, but includes the failed AMC module name together with the message ID in required-element parser failures: `Expected sender and recipient elements for module: dashboard/messages/DMViewMessageModule, message: <id>`.

## Related Issue

Builds on [089-pr-scope-private-message-detail-header.md](089-pr-scope-private-message-detail-header.md) and [184-pr-private-message-detail-fetch-context.md](184-pr-private-message-detail-fetch-context.md), because those drafts established private-message detail parsing as a structural parser boundary and aligned direct detail fetch failures with module/message diagnostics. It also complements [163-pr-private-message-list-row-error-context.md](163-pr-private-message-list-row-error-context.md) and [178-pr-private-message-list-fetch-failure-context.md](178-pr-private-message-list-fetch-failure-context.md), which added module/page context for list-side private-message failures.

No upstream issue was filed from this local workspace.

## Changes

- Reuse the direct detail context formatter for malformed detail HTML parser failures.
- Include module name and message ID when the structural message container is missing.
- Include module name and message ID when the structural message header is missing.
- Include module name and message ID when sender/recipient metadata is malformed.
- Tighten the focused sender/recipient regression to assert module/message context.

## Type Of Change

- Bug fix / diagnostics improvement
- Private-message detail parser context
- Test expectation strengthening

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| Malformed private-message detail HTML still raises `NoElementException`. | `TestPrivateMessageCollection.test_from_ids_missing_sender_or_recipient_raises` provides a detail response with only one `span.printuser` and expects `NoElementException`. | A change that silently accepts malformed sender/recipient metadata, fabricates users, or returns a partial message rejects this local completion claim. |
| The parser error identifies the failed module and message. | The focused regression asserts `Expected sender and recipient elements for module: dashboard/messages/DMViewMessageModule, message: 1`. | The RED test failed before the fix because the message only said `Expected sender and recipient elements for message: 1`. |
| Successful private-message detail parsing remains unchanged. | `uv run pytest tests/unit/test_private_message.py -q` passed 33 tests. | Regressions in successful detail parsing, body/subject spacing, duplicate direct IDs, retry handling, or inbox/sent wrappers reject this local completion claim. |
| Adjacent client/private-message workflows remain green. | `uv run pytest tests/unit/test_client.py tests/unit/test_private_message.py -q` passed 52 tests. | Regressions in client private-message accessors or inbox/sent-box wrappers reject this local completion claim. |
| Broad unit and static quality gates remain green. | `uv run pytest tests/unit -q`; `uv run ruff check src tests`; `uv run ruff format --check src tests`; `uv run mypy src tests`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject this local completion claim. |

## Testing

Implemented locally in commit `3047a93 fix(private_message): include module in detail parse errors`.

- RED: `uv run pytest tests/unit/test_private_message.py::TestPrivateMessageCollection::test_from_ids_missing_sender_or_recipient_raises -q` failed before the fix because the exception message was `Expected sender and recipient elements for message: 1`.
- GREEN: `uv run pytest tests/unit/test_private_message.py::TestPrivateMessageCollection::test_from_ids_missing_sender_or_recipient_raises -q`.
- `uv run pytest tests/unit/test_private_message.py -q` passed 33 tests.
- `uv run pytest tests/unit/test_client.py tests/unit/test_private_message.py -q` passed 52 tests.
- `uv run pytest tests/unit -q` passed 729 tests.
- `uv run ruff check src tests`.
- `uv run ruff format --check src tests`.
- `uv run mypy src tests`.
- `git diff --check`.

Not run successfully: `pyright` because this environment could not find a `pyright` executable.

## Acceptance Criteria

- `PrivateMessageCollection.from_ids(...)` still logs in before non-empty detail reads.
- Empty input still returns an empty collection without login or AMC work.
- Request bodies still use `dashboard/messages/DMViewMessageModule` and `item=<message_id>`.
- `no_message` status still maps to `ForbiddenException`.
- Exhausted detail fetches still raise `UnexpectedException` with module/message context.
- Malformed detail parser failures for missing `div.pmessage`, missing direct `div.header`, or malformed sender/recipient elements now name the same module and message ID.
- Successful detail parsing, duplicate-ID preservation, duplicate response parse reuse, subject/body spacing, inbox/sent wrappers, and send behavior remain unchanged.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Private-message detail parsing can be reached from inbox scans, sent-box scans, and direct `from_id(...)` calls. When a malformed detail response breaks structural parsing, logs should identify the AMC module and message ID so caller-side ledgers can route the failure without storing raw message HTML, body text, account details, credentials, or local rollout paths.

## Local Evidence, Not For Upstream Paste

- Earlier local drafts established private-message detail reads as a practical workflow surface by adding retry-aware list/detail fetches, duplicate direct-ID deduplication, duplicate parse reuse, detail header scoping, list row parser context, and detail fetch module diagnostics.
- Recent context slices showed that aligned module/object identifiers improve resumable multi-account logs without changing successful behavior.
- The refreshed complexity memo continues to list parser/source collection helpers and direct property/parser failure messages as follow-up leads, but this slice only claims private-message detail parser diagnostics.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, raw response HTML, raw message bodies, and account details out of upstream discussion.

## Additional Notes

This slice intentionally does not change request construction, retry policy, `no_message` status classification, duplicate message-ID grouping, response parse reuse, sender/recipient parsing, subject/body spacing, returned `PrivateMessageCollection`, inbox/sent wrappers, private-message sending, or live Wikidot behavior. It only adds module context to existing malformed direct detail parser exception paths.
