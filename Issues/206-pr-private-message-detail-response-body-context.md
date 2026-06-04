# PR Draft: Validate Private Message Detail Response Bodies

## Summary

`PrivateMessageCollection.from_ids(...)` retrieves direct private-message details through `dashboard/messages/DMViewMessageModule` and parses the returned response `body`. Earlier local slices made private-message reads retry-aware, deduplicated direct message IDs, reused duplicate parsed details, scoped detail header parsing, added module/message fetch context, and added module/message parse context. The remaining malformed response path still read `response.json()["body"]`, so an AMC detail response without a `body` field leaked a raw `KeyError`.

This follow-up keeps login checks, request payloads, retry counts, `no_message` handling, duplicate-ID preservation, duplicate parsed-detail reuse, successful sender/recipient parsing, subject/body spacing, date parsing, inbox/sent wrappers, and send behavior unchanged. It only treats a missing detail response `body` as a malformed detail response and raises `NoElementException` with module/message context before BeautifulSoup parsing, user parsing, or date parsing.

## Related Issue

Builds on [037-pr-retry-private-message-fetches.md](037-pr-retry-private-message-fetches.md), [067-pr-deduplicate-direct-private-message-fetches.md](067-pr-deduplicate-direct-private-message-fetches.md), [073-pr-reuse-private-message-detail-parsing.md](073-pr-reuse-private-message-detail-parsing.md), [089-pr-scope-private-message-detail-header.md](089-pr-scope-private-message-detail-header.md), [184-pr-private-message-detail-fetch-context.md](184-pr-private-message-detail-fetch-context.md), and [188-pr-private-message-detail-parse-context.md](188-pr-private-message-detail-parse-context.md). Those drafts established direct private-message detail reads as retry-aware, deduplicated, parser-scoped, and diagnosable without storing raw private-message bodies.

No upstream issue was filed from this local workspace.

## Changes

- Read each direct private-message detail response body with `.get("body")`.
- Convert a missing JSON `body` field into module/message-specific `NoElementException` instead of leaking `KeyError`.
- Add a focused regression for missing detail response body handling.
- Preserve existing malformed HTML element behavior after the response body exists.
- Preserve successful detail parsing, duplicate-ID behavior, inbox/sent wrappers, and send behavior.

## Type Of Change

- Bug fix / diagnostics improvement
- Private-message detail response validation
- Test coverage

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| A direct private-message detail response without JSON `body` still fails before parser work. | `TestPrivateMessageCollection.test_from_ids_missing_detail_response_body_includes_module_and_message_context` returns `{}` from the AMC response and expects `NoElementException`. | A change that raises raw `KeyError`, fabricates an empty body, partially constructs a message, or enters user/date parsing rejects this local completion claim. |
| The malformed detail response error identifies the affected module and message. | The focused regression asserts `Message response body is not found for module: dashboard/messages/DMViewMessageModule, message: 1`. | A generic parser exception without module/message context rejects this local completion claim. |
| Existing private-message detail parsing remains green. | `uv run pytest tests/unit/test_private_message.py -q` passed 34 tests. | Regressions in login checks, request shape, retry handling, `no_message`, duplicate-ID preservation, duplicate parsed-detail reuse, header scoping, sender/recipient parsing, subject/body spacing, date parsing, inbox/sent wrappers, or send behavior reject this local completion claim. |
| Adjacent client/private-message workflows remain green. | `uv run pytest tests/unit/test_client.py tests/unit/test_private_message.py -q` passed 53 tests. | Regressions in client request behavior or private-message workflows reject this local completion claim. |
| Broad unit and static quality gates remain green. | `uv run pytest tests/unit -q`; `uv run ruff check src tests`; `uv run ruff format --check src tests`; `uv run mypy src tests`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject this local completion claim. |

## Testing

Implemented locally in commit `243bffb fix(private_message): validate detail response bodies`.

- RED: `uv run pytest tests/unit/test_private_message.py::TestPrivateMessageCollection::test_from_ids_missing_detail_response_body_includes_module_and_message_context -q` failed before the fix with `KeyError: 'body'`.
- GREEN: `uv run pytest tests/unit/test_private_message.py::TestPrivateMessageCollection::test_from_ids_missing_detail_response_body_includes_module_and_message_context -q`.
- `uv run pytest tests/unit/test_private_message.py -q` passed 34 tests.
- `uv run pytest tests/unit/test_client.py tests/unit/test_private_message.py -q` passed 53 tests.
- `uv run pytest tests/unit -q` passed 739 tests.
- `uv run ruff check src tests`.
- `uv run ruff format --check src tests`.
- `uv run mypy src tests`.
- `git diff --check`.

Not run successfully: `pyright --version` because this environment could not find a `pyright` executable.

## Acceptance Criteria

- Non-empty `PrivateMessageCollection.from_ids(...)` calls still perform the existing login check.
- Empty `PrivateMessageCollection.from_ids(...)` input still performs no login check and no AMC request.
- Direct detail requests still use `dashboard/messages/DMViewMessageModule` and the requested `item` value.
- Missing direct detail response JSON `body` raises `NoElementException` naming the module and message ID.
- Missing structural elements inside an existing response body still use the existing module/message-context `NoElementException` behavior.
- `no_message` responses still resolve to `None` for the requested message.
- Successful detail parsing, duplicate-ID preservation, duplicate parsed-detail reuse, sender/recipient parsing, subject/body spacing, date parsing, inbox/sent wrappers, and send behavior remain unchanged.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Direct private-message detail reads depend on Wikidot returning a JSON `body` field before HTML parsing can start. If that field is missing, wikidot.py should report a structured malformed-response failure with the module and message ID, so caller logs can route the failure without preserving raw response JSON, raw private-message HTML, message bodies, credentials, local rollout paths, or account details.

## Local Evidence, Not For Upstream Paste

- Earlier local drafts established private-message detail acquisition as retry-aware, duplicate-ID-preserving, parse-once, and scoped to generated detail headers.
- Recent context slices showed that compact module/message identifiers improve resumable ledgers without changing successful behavior or storing private message content.
- The refreshed complexity memo continues to list parser/source collection helpers as follow-up leads, but this slice only claims direct private-message detail response-body validation.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, raw response JSON, raw private-message HTML, and message contents out of upstream discussion.

## Additional Notes

This slice intentionally does not change login checks, request module names, retry policy, `no_message` handling, duplicate-ID request deduplication, duplicate parsed-detail reuse, successful sender/recipient/subject/body/date parsing, inbox/sent wrappers, send behavior, or live Wikidot behavior. It only converts a missing direct detail response `body` field into module/message-context `NoElementException` before parser work.
