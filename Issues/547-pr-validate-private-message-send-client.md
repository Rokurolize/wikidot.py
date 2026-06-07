# PR Draft: Validate Private Message Send Client Input

## Summary

`PrivateMessage.send(client, recipient, subject, body)` is the direct browser-free private-message mutation boundary behind `client.private_message.send(...)`. Earlier local slices validated send text inputs, recipient inputs, returned action-status handling, message record fields, direct read client state, and client accessor parent state. One adjacent public send-input gap remained: direct calls such as `PrivateMessage.send(None, valid_user, "Subject", "Body")`, booleans, strings, dictionaries, or arbitrary objects reached `client.login_check()` and leaked raw `AttributeError`.

This change reuses the private-message client validator after subject/body and recipient validation, but before login checks, dashboard message request construction, AMC submission, or returned action-status handling. Malformed direct send clients now raise `ValueError("client must be a Client")` deterministically, while existing text-input precedence, recipient-input precedence, valid send payloads, login-required behavior for valid clients, and action-status diagnostics remain unchanged.

## Outcome

Direct private-message send callers now get deterministic client validation before authenticated mutation work instead of incidental attribute errors from malformed client-like values.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who call private-message sends directly, use client private-message accessors for browser-free notifications, or load send inputs from generated local fixtures where a malformed client should fail before login and request side effects.

## Current Evidence

Local rollout-backed drafts repeatedly identify private-message sends and reads as practical workflow surfaces. Existing drafts [037-pr-retry-private-message-fetches.md](037-pr-retry-private-message-fetches.md), [254-pr-private-message-send-action-status-context.md](254-pr-private-message-send-action-status-context.md), [355-pr-validate-private-message-send-text-inputs.md](355-pr-validate-private-message-send-text-inputs.md), [360-pr-validate-private-message-send-recipients.md](360-pr-validate-private-message-send-recipients.md), [361-pr-validate-private-message-message-id-inputs.md](361-pr-validate-private-message-message-id-inputs.md), [397-pr-validate-private-message-retry-controls.md](397-pr-validate-private-message-retry-controls.md), [425-pr-validate-private-message-collection-initialization.md](425-pr-validate-private-message-collection-initialization.md), [451-pr-validate-private-message-id-field.md](451-pr-validate-private-message-id-field.md), [479-pr-validate-client-accessor-parent-clients.md](479-pr-validate-client-accessor-parent-clients.md), [498-pr-validate-private-message-record-fields.md](498-pr-validate-private-message-record-fields.md), and [546-pr-validate-private-message-read-client.md](546-pr-validate-private-message-read-client.md) establish private-message mutation and read paths, parser diagnostics, retry behavior, ID preflight, collection state, message record state, direct read client state, and accessor parent state as active operational boundaries.

This is not a duplicate of Issue 355. Issue 355 validates `PrivateMessage.send(subject=...)` and `body=...` before login or AMC work. This slice validates the separate caller-provided `client` object after those text fields are known valid.

This is not a duplicate of Issue 360. Issue 360 validates `PrivateMessage.send(recipient=...)` before login or AMC work. This slice validates the separate parent client object after recipient preflight.

This is not a duplicate of Issue 254. Issue 254 validates the returned dashboard message action response after a send request returns. This slice validates send input before login and request work.

This is not a duplicate of Issue 479 or Issue 546. Issue 479 validates client accessor construction, and Issue 546 validates direct private-message detail-read clients. This slice covers the direct send mutation helper `PrivateMessage.send(...)`.

No upstream issue was filed from this local workspace.

## Changes

- Add a focused regression for malformed direct `PrivateMessage.send(client=...)` inputs with otherwise valid recipient and text fields.
- Reuse `_validate_private_message_client(...)` before login and AMC request work.
- Preserve text-field validation, recipient validation, login-required behavior for valid clients, send payload construction, returned action-status diagnostics, and adjacent client/user workflows.

## Type Of Change

- Input validation
- Public mutation-boundary hardening
- Private-message send preflight
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `PrivateMessage.send(None, valid_user, "Subject", "Body")`, `True`, `"test-client"`, `{"username": "test-user"}`, and `object()` must raise `ValueError("client must be a Client")` before login or AMC request work. |
| R2 | Existing malformed subject/body and recipient validation must remain earlier than login and request work, and valid sends must keep the same request payload shape. |
| R3 | Login-required behavior for valid clients and returned action-status diagnostics must remain unchanged. |
| R4 | Private-message, adjacent client/accessor/user, full unit tests, lint, format, mypy, pyright, and whitespace gates must pass before claiming this local implementation complete. |
| R5 | The draft and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private messages, raw rollout paths, pushes, upstream Issues, or upstream PRs. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Malformed direct private-message send clients fail at the public mutation boundary. | `TestPrivateMessage.test_send_rejects_malformed_client_before_login` failed RED for all 5 malformed values with raw `AttributeError`, then passed GREEN after validation was added. | Reaching `client.login_check()`, accepting client-like dictionaries, building send requests, or leaking raw attribute errors rejects this local completion claim. | `PrivateMessage.send(...)` | `src/wikidot/module/private_message.py`, `tests/unit/test_private_message.py` |
| R2 | Existing send input validation and request payload behavior remain stable. | Focused GREEN included `test_send_success`, recipient validation tests, malformed recipient-field tests, and non-string text-input tests. | Changing request fields, accepting malformed text/recipient values, or shifting those paths into request work rejects this local completion claim. | Private-message send inputs | `tests/unit/test_private_message.py` |
| R3 | Valid-client authentication and response diagnostics remain stable. | Focused GREEN included `test_send_requires_login`, `test_send_missing_action_status_includes_recipient_event_and_field_context`, and `test_send_explicit_non_ok_action_status_raises_status_exception`. | Skipping login for valid clients, changing action-status exception classes, or losing recipient/event/field context rejects this local completion claim. | Private-message send auth/action response | `tests/unit/test_private_message.py` |
| R4 | Existing repository quality gates remain green. | The full private-message file passed 117 tests, adjacent client/accessor/user tests passed 100 tests, full unit tests passed 2593 tests, full ruff check and format check passed, full mypy passed with no issues in 87 source files, full pyright passed with 0 errors, 0 warnings, and 0 informations, and `git diff --check` passed. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |
| R5 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level synthetic state; this draft contains no credentials, cookies, auth JSON, raw private-message bodies, live account data, or live site data. | Using real account names, credentials, cookies, auth JSON, sandbox details, raw rollout paths, pushes, upstream Issues, upstream PRs, live Wikidot actions, raw private-message HTML, message text, usernames from private accounts, or private site data rejects this local completion claim. | Test and draft privacy | this draft |

## Testing

Implemented locally in commit `1aaf610 fix(private_message): validate send client`.

- RED: `uv run pytest tests/unit/test_private_message.py::TestPrivateMessage::test_send_rejects_malformed_client_before_login -q` failed 5 tests before the fix because malformed clients reached `client.login_check()` and leaked raw `AttributeError`.
- GREEN focused: `uv run pytest tests/unit/test_private_message.py::TestPrivateMessage::test_send_rejects_malformed_client_before_login tests/unit/test_private_message.py::TestPrivateMessage::test_send_requires_login tests/unit/test_private_message.py::TestPrivateMessage::test_send_success tests/unit/test_private_message.py::TestPrivateMessage::test_send_rejects_non_user_recipient_before_login tests/unit/test_private_message.py::TestPrivateMessage::test_send_rejects_malformed_user_recipient_before_login tests/unit/test_private_message.py::TestPrivateMessage::test_send_rejects_non_string_text_inputs_before_login tests/unit/test_private_message.py::TestPrivateMessage::test_send_missing_action_status_includes_recipient_event_and_field_context tests/unit/test_private_message.py::TestPrivateMessage::test_send_explicit_non_ok_action_status_raises_status_exception -q` passed 15 tests.
- `uv run pytest tests/unit/test_private_message.py -q` passed 117 tests.
- `uv run pytest tests/unit/test_client.py tests/unit/test_client_accessors.py tests/unit/test_user.py -q` passed 100 tests.
- `uv run pytest tests/unit -q` passed 2593 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `uv run mypy .` passed with no issues in 87 source files.
- `uv run pyright .` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- Malformed direct `PrivateMessage.send(client=...)` inputs raise `ValueError("client must be a Client")`.
- Existing text and recipient validation remain login/request preflight checks.
- Valid sends keep their request payload shape and login-required behavior.
- Returned send action-status diagnostics remain unchanged.
- Adjacent client, accessor, and user workflows stay green.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private messages, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Risks And Mitigations

- Risk: Client validation could accidentally change send-input precedence. Mitigation: validation runs after existing subject/body and recipient checks, and focused GREEN includes text and recipient validation tests.
- Risk: The send-client diagnostic could be confused with direct read client validation. Mitigation: both surfaces intentionally share `ValueError("client must be a Client")`, while this draft explicitly covers `PrivateMessage.send(...)` mutation behavior.

## Dependencies

- Existing `Client` remains the canonical parent type for direct private-message sends.
- Existing text and recipient validators remain responsible for payload fields before client validation.
- Existing action-status guard remains responsible for classifying returned Wikidot send responses after a valid client submits a request.

## Open Questions

None for this local slice.

## Upstream-Safe Motivation

`PrivateMessage.send(...)` is the direct mutation entry point for browser-free private-message notifications. Validating the supplied client object before login and request work gives generated callers and tests deterministic errors for malformed inputs without changing live Wikidot behavior, request shape, login-required behavior, send text/recipient validation, or action-status diagnostics.

## Local Evidence, Not For Upstream Paste

- The focused RED failures showed malformed direct `client` arguments crossing the public static send boundary and leaking `AttributeError` from `client.login_check()`.
- This slice only validates the `PrivateMessage.send(...)` caller-provided parent client. It does not change private-message detail acquisition, list acquisition, message ID validation, send retry policy, send payload fields, returned action-status policy, record field validation, live site behavior, or authentication semantics for valid clients.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw private-message HTML, private message text, and private site data out of upstream discussion.
