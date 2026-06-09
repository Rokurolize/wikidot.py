# PR Draft: Validate Private Message Send Status Type

## Summary

`PrivateMessage.send(...)` decodes the send action response and requires a `status` field before treating the send as complete. Issue [254-pr-private-message-send-action-status-context.md](254-pr-private-message-send-action-status-context.md) covered missing status context and explicit non-ok string statuses, but present non-string values such as `{"status": ["not-ok"]}` were still routed into `WikidotStatusCodeException` as if they were real Wikidot status codes. This change rejects malformed generated response data before accepting the send result.

## Outcome

Private-message send workflows now distinguish malformed action-response shape from real Wikidot status-code failures, preserving existing string-status behavior while surfacing type-corrupt generated responses with recipient, event, field, and type context.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators using browser-free private-message send, notification, migration, test-fixture, or moderation workflows where send responses may come from synthetic tests, recorded traffic, adapters, or generated data.

## Current Evidence

Local rollout-backed drafts already identify private-message read and send paths as practical shared workflows. Existing drafts [037-pr-retry-private-message-fetches.md](037-pr-retry-private-message-fetches.md), [054-pr-deduplicate-private-message-detail-fetches.md](054-pr-deduplicate-private-message-detail-fetches.md), [067-pr-deduplicate-direct-private-message-fetches.md](067-pr-deduplicate-direct-private-message-fetches.md), [073-pr-reuse-private-message-detail-parsing.md](073-pr-reuse-private-message-detail-parsing.md), [077-pr-skip-empty-private-message-fetch-batches.md](077-pr-skip-empty-private-message-fetch-batches.md), [119-pr-preserve-private-message-subject-spacing.md](119-pr-preserve-private-message-subject-spacing.md), [254-pr-private-message-send-action-status-context.md](254-pr-private-message-send-action-status-context.md), [273-pr-private-message-detail-subject-body-context.md](273-pr-private-message-detail-subject-body-context.md), [321-pr-private-message-response-body-type-context.md](321-pr-private-message-response-body-type-context.md), [355-pr-validate-private-message-send-text-inputs.md](355-pr-validate-private-message-send-text-inputs.md), [360-pr-validate-private-message-send-recipients.md](360-pr-validate-private-message-send-recipients.md), and [547-pr-validate-private-message-send-client.md](547-pr-validate-private-message-send-client.md) cover retry, batching, parsing, text input, recipient, client, body-shape, and missing/non-ok send status behavior.

Issue [403-pr-validate-amc-response-status-type.md](403-pr-validate-amc-response-status-type.md) is not a duplicate: it covers raw Ajax Module Connector response status typing before module-level dispatch. Issue [714-pr-validate-page-save-status-type.md](714-pr-validate-page-save-status-type.md) is also not a duplicate: it covers the page `savePage` action response consumed by `Page.create_or_edit(...)`. This slice validates the module-level private-message send action response consumed by `PrivateMessage.send(...)`. No upstream issue was filed from this local workspace.

## Changes

- Add a type guard in the private-message send action status extractor.
- Raise `NoElementException` for a present non-string `status` with recipient, id, event, field, expected type, and actual type context.
- Preserve the Issue 254 missing-status diagnostic.
- Preserve explicit non-ok string handling through `WikidotStatusCodeException`.
- Add a focused regression proving malformed status types are decoded once and rejected as malformed action-response shape.

## Type Of Change

- Response-shape validation
- Private-message send action hardening
- Generated response data diagnostics
- Regression tests

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `PrivateMessage.send(...)` must reject a non-string send response `status` with `NoElementException` containing recipient, id, event, `field=status`, `expected=str`, and the actual type. |
| R2 | A missing `status` field must keep the existing Issue 254 missing-status diagnostic. |
| R3 | Explicit non-ok string statuses must still raise `WikidotStatusCodeException` and must not be reclassified as malformed shape. |
| R4 | The send response body must still be decoded once for the malformed status path. |
| R5 | Adjacent private-message send and read behavior must remain green. |
| R6 | The draft and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | `{"status": ["not-ok"]}` fails with malformed send action status context before completion is accepted. | `test_send_malformed_action_status_type_includes_recipient_event_and_type_context` failed RED with `WikidotStatusCodeException`, then passed GREEN after status typing was added. | Treating a list, dict, number, or object as a Wikidot status code rejects this local completion claim. | Private-message send response shape | `src/wikidot/module/private_message.py`, `tests/unit/test_private_message.py` |
| R2 | `{}` still raises the Issue 254 missing-status message with recipient, id, event, and field context. | `test_send_missing_action_status_includes_recipient_event_and_field_context` passed unchanged. | Changing the missing-status exception type, dropping context, or masking it behind status-code handling rejects this local completion claim. | Private-message send missing field handling | `src/wikidot/module/private_message.py`, `tests/unit/test_private_message.py` |
| R3 | `{"status": "not_ok"}` still routes through `WikidotStatusCodeException`. | `test_send_explicit_non_ok_action_status_raises_status_exception` passed unchanged. | Reclassifying non-ok strings as malformed response shape rejects this local completion claim. | Private-message send status-code handling | `tests/unit/test_private_message.py` |
| R4 | The malformed status path decodes the send response JSON once. | The new regression asserts `mock_response.json.call_count == 1`. | Reintroducing duplicate decode work or hidden side effects rejects this local completion claim. | Private-message send response decoding | `tests/unit/test_private_message.py` |
| R5 | Adjacent private-message behavior remains stable. | `TestPrivateMessage` passed 72 tests and `tests/unit/test_private_message.py` passed 168 tests. | Regressing private-message send validation, list/detail parsing, collection behavior, or fetch behavior rejects this local completion claim. | Private-message workflows | `tests/unit/test_private_message.py` |
| R6 | No live site state or private material is needed to prove the behavior. | The regression uses synthetic unit-level response bodies and mocks only. | Using real account names, credentials, cookies, auth JSON, sandbox details, raw response bodies, live Wikidot actions, private content, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs rejects this local completion claim. | Test and draft privacy | this draft |

## Testing

Implemented locally in commit `c3f6c35 fix(private_message): validate send status type`.

- RED: `uv run pytest tests/unit/test_private_message.py::TestPrivateMessage::test_send_malformed_action_status_type_includes_recipient_event_and_type_context -q` failed before the fix with `WikidotStatusCodeException` instead of the expected malformed-shape `NoElementException`.
- GREEN focused: `uv run pytest tests/unit/test_private_message.py::TestPrivateMessage::test_send_missing_action_status_includes_recipient_event_and_field_context tests/unit/test_private_message.py::TestPrivateMessage::test_send_explicit_non_ok_action_status_raises_status_exception tests/unit/test_private_message.py::TestPrivateMessage::test_send_malformed_action_status_type_includes_recipient_event_and_type_context -q` passed 3 tests.
- `uv run pytest tests/unit/test_private_message.py::TestPrivateMessage -q` passed 72 tests.
- `uv run pytest tests/unit/test_private_message.py -q` passed 168 tests.
- `uv run ruff format src/wikidot/module/private_message.py tests/unit/test_private_message.py` left both files unchanged.
- `uv run ruff check src/wikidot/module/private_message.py tests/unit/test_private_message.py` passed.
- `git diff --check` passed.

## Acceptance Criteria

- `{"status": ["not-ok"]}` raises `NoElementException` with recipient, id, event, `field=status`, `expected=str`, and `actual=list` context.
- `{}` still raises the existing missing-status message from Issue 254.
- `{"status": "not_ok"}` still raises `WikidotStatusCodeException`.
- The malformed non-string status path still decodes the response JSON once.
- The new test uses unit-level synthetic values only and does not require live Wikidot, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.
- Private-data and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: A caller may have relied on a non-string `status` object being formatted into a `WikidotStatusCodeException`. Mitigation: Wikidot action statuses are strings, Issue 403 already validates raw AMC statuses as strings, and module-level action responses should reject malformed generated data before business handling.
- Risk: This could be confused with raw AMC response typing. Mitigation: Issue 403 covers the raw connector response envelope; this slice covers the private-message send action payload used by `PrivateMessage.send(...)`.
- Risk: This could be confused with page save status typing. Mitigation: Issue 714 covers `Page.create_or_edit(...)`; this slice covers `PrivateMessage.send(...)`.
- Risk: Tightening send response shape could hide legitimate non-ok Wikidot string statuses. Mitigation: non-ok strings are deliberately preserved on the existing `WikidotStatusCodeException` path.
- Risk: The error could become too generic for generated fixtures. Mitigation: the diagnostic names the recipient, id, event, field, expected type, and actual type.

## Dependencies

- Existing `PrivateMessage.send(...)` remains responsible for send orchestration.
- Existing `WikidotStatusCodeException` handling remains responsible for explicit non-ok string statuses.
- Existing `NoElementException` remains the parser/data-shape exception for missing or malformed response fields.
- No new dependency, live Wikidot action, credential, or upstream API change is required.

## Open Questions

None for this local slice. Remaining useful work should continue with fresh duplicate-checked public input boundaries, parser diagnostics, result ergonomics, action/read boundaries, or complexity candidates outside this now-covered private-message send status type path.

## Upstream-Safe Motivation

`PrivateMessage.send(...)` treats send action responses as status-bearing action payloads. Rejecting malformed status types at that boundary keeps generated or adapted response data from masquerading as a real Wikidot status code and makes send failures easier to diagnose.

## Local Evidence, Not For Upstream Paste

- Local rollout-backed work established private-message send, fetch, detail parse, generated-fixture, migration, notification, and moderation workflows as practical consumers of private-message behavior.
- Existing send and raw AMC drafts covered missing send status context, explicit non-ok send strings, and raw connector envelope status typing; they did not validate the module-level private-message send action status type.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw HTTP bodies, private content, private site data, and source text from real sites out of upstream discussion.
