# PR Draft: Validate Private Message Send Response Payload

## Summary

`PrivateMessage.send(...)` now validates that the decoded send action response is a dictionary before reading its `status` field. Non-mapping payloads such as `["not-ok"]` raise contextual `NoElementException` with recipient, user ID, event, expected type, and actual type context instead of leaking a raw list-index `TypeError`.

The change is intentionally narrow: valid `{"status": "ok"}` sends, missing `status` diagnostics, non-string `status` diagnostics, and explicit non-ok string status handling remain unchanged.

## Problem Statement

`PrivateMessage.send(...)` treats the response from the dashboard message action as a status-bearing JSON object. Earlier local slices covered missing `status`, explicit non-ok string statuses, malformed non-string `status` values, text inputs, recipient validation, and client validation. One response-shape gap remained: if `response.json()` returned a non-dictionary payload, `_require_private_message_send_action_status(...)` attempted `data["status"]` and leaked a raw `TypeError`.

That failure gives callers neither the private-message send context nor a stable wikidot.py data-shape exception. Generated fixtures, adapters, recorded traffic, or mocked responses should be classified before field access.

## Rollout Evidence

Local rollout-backed drafts repeatedly identify private-message send and read workflows as practical automation surfaces: [037-pr-retry-private-message-fetches.md](037-pr-retry-private-message-fetches.md), [054-pr-deduplicate-private-message-detail-fetches.md](054-pr-deduplicate-private-message-detail-fetches.md), [067-pr-deduplicate-direct-private-message-fetches.md](067-pr-deduplicate-direct-private-message-fetches.md), [073-pr-reuse-private-message-detail-parsing.md](073-pr-reuse-private-message-detail-parsing.md), [077-pr-skip-empty-private-message-fetch-batches.md](077-pr-skip-empty-private-message-fetch-batches.md), [119-pr-preserve-private-message-subject-spacing.md](119-pr-preserve-private-message-subject-spacing.md), [254-pr-private-message-send-action-status-context.md](254-pr-private-message-send-action-status-context.md), [321-pr-private-message-response-body-type-context.md](321-pr-private-message-response-body-type-context.md), [355-pr-validate-private-message-send-text-inputs.md](355-pr-validate-private-message-send-text-inputs.md), [360-pr-validate-private-message-send-recipients.md](360-pr-validate-private-message-send-recipients.md), [547-pr-validate-private-message-send-client.md](547-pr-validate-private-message-send-client.md), and [715-pr-validate-private-message-send-status-type.md](715-pr-validate-private-message-send-status-type.md).

This slice is not a duplicate of [254-pr-private-message-send-action-status-context.md](254-pr-private-message-send-action-status-context.md). Issue 254 covered a mapping response that omitted `status`.

This slice is not a duplicate of [715-pr-validate-private-message-send-status-type.md](715-pr-validate-private-message-send-status-type.md). Issue 715 covered a present non-string `status` field inside a mapping, such as `{"status": ["not-ok"]}`. This slice covers the decoded action response payload not being a mapping before `status` lookup starts.

Issue [403-pr-validate-amc-response-status-type.md](403-pr-validate-amc-response-status-type.md) is not a duplicate because it covers the raw Ajax Module Connector response envelope before module-level action payload handling.

No upstream issue was filed from this local workspace.

## Affected Workflows

- Browser-free private-message sends through `PrivateMessage.send(...)`.
- `Client.private_message.send(...)` and generated or fixture-driven send workflows.
- Synthetic response adapters and recorded-response tests that decode action responses before returning them to wikidot.py module code.

## Proposed Fix

- Change `_require_private_message_send_action_status(...)` to accept an object payload.
- Reject non-dictionary payloads with `NoElementException` before field access.
- Include only structural context and type names in the diagnostic, not raw response data.
- Preserve existing missing-status, malformed-status-type, non-ok string, and success behavior.

## Implementation Notes

Implemented locally in commit `504ccef fix(private_message): validate send response payload`.

The implementation adds one preflight guard in `src/wikidot/module/private_message.py`:

```python
if not isinstance(data, dict):
    raise exceptions.NoElementException(
        f"Private message send action response is malformed for recipient: {recipient.name} "
        f"(id={recipient.id}, event={event}, expected=dict, actual={type(data).__name__})"
    )
```

The RED regression mocked `response.json()` as `["not-ok"]`. Before the fix, the helper leaked `TypeError: list indices must be integers or slices, not str`. After the fix, the same case raises the contextual `NoElementException` and decodes the response once.

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| Non-dictionary private-message send action payloads fail before `status` lookup. | `test_send_malformed_action_response_type_includes_recipient_event_and_type_context` failed RED with raw `TypeError`, then passed GREEN. | Reaching list indexing, leaking `TypeError`, coercing the payload, or treating a list as a status response rejects this claim. |
| Missing `status` in a dictionary keeps the existing Issue 254 diagnostic. | Focused GREEN included `test_send_missing_action_status_includes_recipient_event_and_field_context`. | Reclassifying `{}` as the payload-type branch or dropping `field=status` rejects this claim. |
| Present non-string `status` keeps the existing Issue 715 diagnostic. | Focused GREEN included `test_send_malformed_action_status_type_includes_recipient_event_and_type_context`. | Reclassifying `{"status": ["not-ok"]}` as a payload-type error or treating the list as a status code rejects this claim. |
| Explicit non-ok string statuses still use `WikidotStatusCodeException`. | Focused GREEN included `test_send_explicit_non_ok_action_status_raises_status_exception`. | Reclassifying non-ok strings as malformed response shape rejects this claim. |
| Adjacent private-message behavior remains stable. | `tests/unit/test_private_message.py` passed 180 tests and `TestClientPrivateMessageAccessor` passed 10 tests. | Regressing private-message parsing, lookup, send validation, or client accessor behavior rejects this claim. |
| Repository quality gates remain green. | Full unit passed 3904 tests; ruff, format check, mypy, pyright, whitespace, Brooks focused review, and Clawpatch provenance checks passed. | Test, lint, format, type, whitespace, review, or unreported tooling failures reject this claim. |

## Tests and Verification

Implemented locally in commit `504ccef fix(private_message): validate send response payload`.

- RED: `uv run pytest tests/unit/test_private_message.py::TestPrivateMessage::test_send_malformed_action_response_type_includes_recipient_event_and_type_context -q --tb=short` failed before the fix with raw `TypeError: list indices must be integers or slices, not str`.
- GREEN focused: `uv run pytest tests/unit/test_private_message.py::TestPrivateMessage::test_send_missing_action_status_includes_recipient_event_and_field_context tests/unit/test_private_message.py::TestPrivateMessage::test_send_malformed_action_response_type_includes_recipient_event_and_type_context tests/unit/test_private_message.py::TestPrivateMessage::test_send_malformed_action_status_type_includes_recipient_event_and_type_context tests/unit/test_private_message.py::TestPrivateMessage::test_send_explicit_non_ok_action_status_raises_status_exception -q --tb=short` passed 4 tests.
- Private-message coverage: `uv run pytest tests/unit/test_private_message.py -q --tb=short` passed 180 tests.
- Client accessor coverage: `uv run pytest tests/unit/test_client.py::TestClientPrivateMessageAccessor -q --tb=short` passed 10 tests.
- Full unit: `uv run pytest tests/unit -q --tb=short` passed 3904 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files, plus existing notes about unchecked untyped function bodies and the existing unused-section note from `pyproject.toml`.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.
- Brooks focused changed-file review found no blocking findings. Full Brooks sweep was not run because the skill requires explicit full-repository auto-fix consent.
- Clawpatch local provenance check passed: local fork commit `d89ca91`, provider `codex-cli 0.139.0`, doctor state `missing`, secrets redacted, launcher SHA256 `6527a7f968bca0e270cb98fa4e6b7707ca951868309562078e518faefa6726b8`.

## Acceptance Criteria

- `PrivateMessage.send(...)` with `response.json()` returning `["not-ok"]` raises `NoElementException` matching `Private message send action response is malformed for recipient: test-user (id=12345, event=send, expected=dict, actual=list)`.
- `{}` still raises the existing missing-status message with `field=status`.
- `{"status": ["not-ok"]}` still raises the existing malformed status-type message with `expected=str, actual=list`.
- `{"status": "not_ok"}` still raises `WikidotStatusCodeException`.
- The malformed payload branch decodes the response JSON once and does not include raw response data.
- The new test uses unit-level synthetic values only and does not require live Wikidot, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.
- Private-data and local-path leak checks over the new draft pass before finalizing the slice.

## Compatibility and Risk Notes

- Risk: A caller may have relied on raw `TypeError` from malformed synthetic responses. Mitigation: the public module expects a status-bearing JSON object, and repo validation style consistently routes malformed generated response shape through contextual `NoElementException`.
- Risk: This could be confused with status-field validation. Mitigation: missing and non-string `status` branches are preserved and tested separately.
- Risk: This could hide raw payload details useful for debugging. Mitigation: the diagnostic includes recipient, ID, event, expected type, and actual type while avoiding raw response data that could contain private message content or account material.

## Dependencies

- Private-message send responses remain expected to decode as JSON objects with string `status` fields.
- `WikidotStatusCodeException` remains responsible for explicit non-ok string statuses.
- `NoElementException` remains the parser/data-shape exception for malformed module response payloads.

## Open Questions

None for this local slice. Similar non-mapping action-payload guards may be useful on other mutation helpers, but each surface should receive its own duplicate check against the existing action-status and status-type issue series before implementation.

## Rationale for Upstream Suitability

The patch is small, local, and consistent with existing wikidot.py response-shape diagnostics. It improves failure classification for malformed private-message send responses without changing successful sends, documented input validation, or existing status-code behavior.

## Local Evidence

- Local rollout-backed private-message drafts established send, fetch, detail parsing, generated-fixture, migration, notification, and moderation workflows as practical consumers of private-message behavior.
- Existing local drafts covered missing send status context, present non-string send status values, raw connector envelope status typing, send text validation, recipient validation, and send client validation. They did not cover a decoded action response payload that is not a mapping before `status` lookup.
- This slice only validates private-message send action payload shape. It does not change request construction, login checks, retry behavior, response-body parsing, inbox/sent-box reads, direct message lookup, live Wikidot behavior, pushes, upstream Issues, or upstream PRs.
- Keep private rollout paths, credentials, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, cookies, auth JSON, raw private-message content, raw response bodies, private site data, and private source text out of upstream discussion.
