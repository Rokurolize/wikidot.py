# PR Draft: Include Module Context In Private Message Detail Failures

## Summary

`PrivateMessageCollection.from_ids(...)` retrieves direct private-message details through `dashboard/messages/DMViewMessageModule`. Earlier local slices made private-message detail reads retry-aware, deduplicated duplicate direct IDs, reused duplicate parsed detail responses, scoped detail-header parsing, and added module/page context to private-message list fetch failures, but the direct detail failure messages still only named the message ID.

This follow-up keeps login checks, request payloads, retry counts, non-retryable `no_message` handling, duplicate-ID preservation, successful parsing, sender/recipient parsing, subject/body text spacing, and exception types unchanged, but includes the failed AMC module name together with the message ID in direct detail failures: `Cannot retrieve private message for module: dashboard/messages/DMViewMessageModule, message: <id>`.

## Related Issue

Builds on [037-pr-retry-private-message-fetches.md](037-pr-retry-private-message-fetches.md), [054-pr-deduplicate-private-message-detail-fetches.md](054-pr-deduplicate-private-message-detail-fetches.md), [067-pr-deduplicate-direct-private-message-fetches.md](067-pr-deduplicate-direct-private-message-fetches.md), [073-pr-reuse-private-message-detail-parsing.md](073-pr-reuse-private-message-detail-parsing.md), [089-pr-scope-private-message-detail-header.md](089-pr-scope-private-message-detail-header.md), [163-pr-private-message-list-row-error-context.md](163-pr-private-message-list-row-error-context.md), and [178-pr-private-message-list-fetch-failure-context.md](178-pr-private-message-list-fetch-failure-context.md), because those drafts established private-message list and detail acquisition as retry-aware, parser-boundary-sensitive, rollout-backed read surfaces.

No upstream issue was filed from this local workspace.

## Changes

- Include the private-message detail AMC module name in exhausted retry failures.
- Include the private-message detail AMC module name in `no_message` forbidden failures.
- Centralize the compact direct-detail fetch context formatter beside the existing list fetch context helpers.
- Tighten focused regressions for retry exhaustion and forbidden detail status messages.
- Preserve successful detail parsing, duplicate message ID behavior, retry semantics, exception classes, and public collection shape.

## Type Of Change

- Bug fix / diagnostics improvement
- Private-message detail fetch failure context
- Test update

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| Exhausted retry for direct private-message detail fetches still raises `UnexpectedException`. | `TestPrivateMessageCollection.test_from_ids_raises_when_detail_retry_is_exhausted` forces retry exhaustion and expects `UnexpectedException`. | Returning an empty collection, omitting the message, caching a partial result, or changing the exception type rejects this local completion claim. |
| Retry-exhausted detail failures identify the failed module and message ID. | The focused regression asserts `Cannot retrieve private message for module: dashboard/messages/DMViewMessageModule, message: 1`. | The RED test failed before the fix because the message was only `Cannot retrieve private message: 1`. |
| `no_message` detail status still maps to `ForbiddenException`. | `TestPrivateMessageCollection.test_from_ids_forbidden_error` still receives a `ForbiddenException`. | Re-raising `WikidotStatusCodeException`, retrying `no_message`, or changing successful access behavior rejects this local completion claim. |
| Forbidden detail failures identify the failed module and message ID. | The focused regression asserts `Failed to get private message for module: dashboard/messages/DMViewMessageModule, message: 1`. | The RED test failed before the fix because the message was only `Failed to get message: 1`. |
| Private-message behavior remains green. | `uv run pytest tests/unit/test_private_message.py -q` passed 33 tests. | Regressions in login checks, empty input, transient retry success, duplicate-ID ordering, parsed body/subject spacing, inbox/sent list acquisition, or direct `PrivateMessage.from_id(...)` reject this local completion claim. |
| Broad unit and static quality gates remain green. | `uv run pytest tests/unit -q`; `uv run ruff check src tests`; `uv run ruff format --check src tests`; `uv run mypy src tests`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject this local completion claim. |

## Testing

Implemented locally in commit `329bfe0 fix(private_message): include module in detail failures`.

- RED: `uv run pytest tests/unit/test_private_message.py::TestPrivateMessageCollection::test_from_ids_forbidden_error tests/unit/test_private_message.py::TestPrivateMessageCollection::test_from_ids_raises_when_detail_retry_is_exhausted -q` failed before the fix because forbidden detail status only said `Failed to get message: 1` and retry exhaustion only said `Cannot retrieve private message: 1`.
- GREEN: `uv run pytest tests/unit/test_private_message.py::TestPrivateMessageCollection::test_from_ids_forbidden_error tests/unit/test_private_message.py::TestPrivateMessageCollection::test_from_ids_raises_when_detail_retry_is_exhausted -q`.
- `uv run pytest tests/unit/test_private_message.py -q` passed 33 tests.
- `uv run pytest tests/unit -q` passed 727 tests.
- `uv run ruff check src tests`.
- `uv run ruff format --check src tests`.
- `uv run mypy src tests`.
- `git diff --check`.

Not run successfully: `pyright` because this environment could not find a `pyright` executable.

## Acceptance Criteria

- `PrivateMessageCollection.from_ids(...)` still logs in, deduplicates request IDs, uses the same `dashboard/messages/DMViewMessageModule` request body, and preserves duplicate output entries in caller order.
- If a direct detail request exhausts retry, the method raises `UnexpectedException` naming both the AMC module and failed message ID.
- If Wikidot reports `no_message`, the method still raises `ForbiddenException` while naming both the AMC module and failed message ID.
- Successful sender, recipient, subject, body, and date parsing remain unchanged.
- Inbox and sent-box list acquisition remain unchanged except for continuing to call the same direct detail helper after collecting IDs.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Private-message detail fetches can run from inbox scans, sent-box scans, and direct `from_id(...)` calls. When a detail fetch fails, logs should identify the failed AMC module as well as the message ID so callers can route failures without storing raw response HTML, message body text, credentials, local rollout paths, or account details.

## Local Evidence, Not For Upstream Paste

- Earlier local drafts established private-message reads as practical workflow surfaces by adding retry-aware list/detail fetches, duplicate direct-ID deduplication, duplicate parse reuse, list row parser context, detail header scoping, and list fetch module/page diagnostics.
- Recent context slices showed that compact module/object identifiers improve resumable ledgers without changing successful behavior.
- This slice only claims direct detail failure diagnostics. It does not claim any live Wikidot behavior change.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, raw response HTML, and saved message contents out of upstream discussion.

## Additional Notes

This slice intentionally does not change request module names, request bodies, retry policy, `no_message` status classification, duplicate message-ID grouping, response parse reuse, sender/recipient parsing, subject/body spacing, returned `PrivateMessageCollection`, inbox/sent wrappers, private-message sending, or live Wikidot behavior. It only adds module context to existing direct private-message detail failure messages.
