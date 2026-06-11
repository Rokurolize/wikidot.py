# PR Draft: Validate Private Message Detail Response Payloads

## Summary

`PrivateMessageCollection.from_ids(...)` fetches direct private-message detail pages through `dashboard/messages/DMViewMessageModule`, deduplicates repeated message IDs, and parses the detail response into sender, recipient, subject, body, and timestamp fields. The detail parser already converted missing `body` fields and present non-string `body` values into contextual `NoElementException` diagnostics, but it still assumed `response.json()` returned a mapping before calling `.get("body")`.

This change validates the decoded detail response payload root before reading `body`. A non-mapping private-message detail payload now raises `NoElementException` with the dashboard module name, message ID, expected root type, and observed type. Existing missing-body and malformed-body diagnostics remain distinct, and no raw response JSON, private-message HTML, subjects, bodies, credentials, cookies, auth JSON, local rollout paths, or account material is included.

## Related Issue

Builds on [206-pr-private-message-detail-response-body-context.md](206-pr-private-message-detail-response-body-context.md), [321-pr-private-message-response-body-type-context.md](321-pr-private-message-response-body-type-context.md), [807-pr-validate-private-message-send-response-payload.md](807-pr-validate-private-message-send-response-payload.md), and [822-pr-validate-private-message-list-response-payload.md](822-pr-validate-private-message-list-response-payload.md).

This is not a duplicate of Issue 206 because that draft covered mapping responses with missing `body`. It is not a duplicate of Issue 321 because that draft covered mapping responses whose present `body` value had the wrong type. It is not a duplicate of Issue 822 because that draft covered private-message list pages, not direct detail pages. It is not a duplicate of Issue 807 because that draft covered send action response payloads, not read response payloads.

No upstream issue was filed from this local workspace.

## Changes

- Validate that the private-message detail response payload returned by `response.json()` is a mapping before reading `body`.
- Raise module/message-specific `NoElementException` for non-mapping detail payload roots.
- Add a focused direct detail acquisition regression for a list-valued payload root.
- Preserve existing missing-body, non-string-body, parser, duplicate-ID, retry, inbox/sent wrapper, collection, and send behavior.

## Type Of Change

- Bug fix / diagnostics improvement
- Private-message detail response payload validation
- Test coverage

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| A non-mapping private-message detail response payload fails before body extraction or detail parsing. | `TestPrivateMessageCollection.test_from_ids_malformed_detail_response_payload_type_includes_module_message_and_type_context` returns `["not", "a", "mapping"]` from the detail AMC response and expects `NoElementException`. | Leaking `AttributeError`, parsing sender/recipient/date/subject/body fields, constructing a message, or omitting module/message/type context rejects this local completion claim. |
| Existing missing-body and malformed-body diagnostics remain distinct. | Focused GREEN included `test_from_ids_missing_detail_response_body_includes_module_and_message_context` and `test_from_ids_malformed_detail_response_body_type_includes_module_message_and_type_context`. | Reclassifying `{}` or `{"body": ["not-html"]}` as a payload-root error, dropping `field=body`, or changing the existing messages rejects this local completion claim. |
| Existing private-message behavior remains compatible. | `uv run pytest tests/unit/test_private_message.py -q` passed 182 tests. | Regressing client validation, login checks, retry behavior, duplicate-ID deduplication, detail parsing, parser diagnostics, inbox/sent wrappers, collection behavior, or send behavior rejects this local completion claim. |
| Broad unit and static gates remain green. | `uv run pytest tests/unit -q` passed 3920 tests; `uv run ruff check .`; `uv run ruff format --check .`; `uv run mypy src tests`; `uv run pyright`; `git diff --check`. | Any failed unit, lint, format, type, pyright, or whitespace gate rejects this local completion claim. |
| Diagnostics remain privacy-preserving. | The new message includes only module name, message ID, expected root type, and observed type. | Including raw response JSON, generated private-message HTML, message subjects, message bodies, credentials, cookies, auth JSON, local rollout paths, account material, or private site data rejects this local completion claim. |

## Testing

Implemented locally in commit `c7ff0d6 fix(private_message): validate detail response payload`.

- RED: `uv run pytest tests/unit/test_private_message.py::TestPrivateMessageCollection::test_from_ids_malformed_detail_response_payload_type_includes_module_message_and_type_context -q` failed before the fix with `AttributeError: 'list' object has no attribute 'get'`.
- GREEN: `uv run pytest tests/unit/test_private_message.py::TestPrivateMessageCollection::test_from_ids_missing_detail_response_body_includes_module_and_message_context tests/unit/test_private_message.py::TestPrivateMessageCollection::test_from_ids_malformed_detail_response_body_type_includes_module_message_and_type_context tests/unit/test_private_message.py::TestPrivateMessageCollection::test_from_ids_malformed_detail_response_payload_type_includes_module_message_and_type_context -q` passed 3 tests.
- `uv run pytest tests/unit/test_private_message.py -q` passed 182 tests.
- `uv run pytest tests/unit -q` passed 3920 tests.
- `uv run ruff check .`.
- `uv run ruff format --check .`.
- `uv run mypy src tests` passed with existing notes about unchecked untyped function bodies and the unused `pyproject.toml` lxml module section.
- `uv run pyright`.
- `git diff --check`.

## Acceptance Criteria

- `PrivateMessageCollection.from_ids(...)`, `PrivateMessage.from_id(...)`, inbox/sent wrappers, and client private-message accessors still use the same direct detail acquisition path.
- A list-valued decoded response payload for a private-message detail page raises `NoElementException` matching `Message response payload is malformed for module: dashboard/messages/DMViewMessageModule, message: 1 (expected=dict, actual=list)`.
- Mapping payloads without `body` still raise the existing missing-body message.
- Mapping payloads with non-string `body` still raise the existing malformed-body message with `field=body`, `expected=str`, and the observed body type.
- Successful detail parsing, retry behavior, duplicate-ID deduplication, parser context, inbox/sent wrappers, collection behavior, and send behavior remain unchanged.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Private-message detail acquisition cannot safely parse detail pages unless the AMC JSON root is a mapping with a `body` field. Rejecting non-mapping roots at the response boundary keeps caller diagnostics compact and actionable while avoiding raw private-message content or response payload disclosure.

## Local Evidence, Not For Upstream Paste

- Issue 206 established missing private-message detail body context.
- Issue 321 established present non-string private-message detail body context.
- Issue 822 established the adjacent private-message list response payload root guard.
- The broader response-payload series applied the same boundary distinction to action responses and list/read responses across site applications, forum categories, site members, forum post revisions, and private-message lists.
- Complexity scanning reported no obvious hotspots in `src/wikidot/module/private_message.py`; this slice did not introduce a new abstraction or alter acquisition control flow.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, cookies, auth JSON, raw response JSON, private-message HTML, message subjects, message bodies, and private site content out of upstream discussion.

## Additional Notes

This slice intentionally does not change client validation, login checks, request payloads, retry policy, duplicate-ID deduplication, detail parser rules, inbox/sent wrappers, collection APIs, send behavior, live Wikidot behavior, or upstream filing state. It only validates the decoded private-message detail response payload root before the existing `body` validation.
