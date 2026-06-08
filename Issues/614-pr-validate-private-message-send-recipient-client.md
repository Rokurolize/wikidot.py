# PR Draft: Validate PrivateMessage Send Recipient Client

## Summary

`PrivateMessage.send(client, recipient, subject, body)` accepts a caller-provided `Client` and `User` recipient, then submits `recipient.id` through the caller-provided client. Earlier local slices validate send text inputs, recipient shape, direct send client type, and stored `PrivateMessage` participant/client coherence. One adjacent mutation-boundary gap remained: a valid `User` object from a different `Client` context could still be passed as the send recipient and progress into login, AMC request construction, and returned action-status handling under the wrong parent client.

This change reuses the private-message user/client coherence validator after subject/body, recipient-shape, and client-type validation, but before `client.login_check()` or dashboard message request construction. Mismatched recipients now raise `ValueError("recipient must belong to the client")`. Valid sends, malformed text precedence, malformed recipient-shape precedence, malformed client precedence, request payload shape, login-required behavior for valid clients, and returned action-status diagnostics remain unchanged.

## Outcome

Direct private-message sends cannot combine a sending `Client` with a recipient `User` object owned by a different client context.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who call `PrivateMessage.send(...)` or `client.private_message.send(...)` for browser-free notifications, moderation messages, migration notices, workflow status messages, or generated local fixtures where recipient objects may come from cached or separately constructed clients.

## Current Evidence

Local rollout-backed drafts repeatedly identify private-message sends and reads as practical workflow surfaces. Existing drafts [037-pr-retry-private-message-fetches.md](037-pr-retry-private-message-fetches.md), [254-pr-private-message-send-action-status-context.md](254-pr-private-message-send-action-status-context.md), [355-pr-validate-private-message-send-text-inputs.md](355-pr-validate-private-message-send-text-inputs.md), [360-pr-validate-private-message-send-recipients.md](360-pr-validate-private-message-send-recipients.md), [397-pr-validate-private-message-retry-controls.md](397-pr-validate-private-message-retry-controls.md), [498-pr-validate-private-message-record-fields.md](498-pr-validate-private-message-record-fields.md), [546-pr-validate-private-message-read-client.md](546-pr-validate-private-message-read-client.md), [547-pr-validate-private-message-send-client.md](547-pr-validate-private-message-send-client.md), [555-pr-validate-private-message-mailbox-client.md](555-pr-validate-private-message-mailbox-client.md), [612-pr-validate-private-message-record-client.md](612-pr-validate-private-message-record-client.md), and [613-pr-validate-private-message-participant-clients.md](613-pr-validate-private-message-participant-clients.md) establish private-message acquisition, parsing, mutation, collection state, record-state validation, and parent-client validation as active operational boundaries.

This is not a duplicate of Issue 360. Issue 360 validates that the send recipient is a `User` with usable `id` and `name`; it does not validate that the recipient's `client` is the same client that will submit the send request.

This is not a duplicate of Issue 547. Issue 547 validates the caller-provided send `client` object itself; it does not validate the relationship between a valid client and a valid recipient.

This is not a duplicate of Issue 613. Issue 613 validates stored `PrivateMessage(...)` sender and recipient coherence at record construction. This slice validates direct send mutation inputs before login or AMC work.

No upstream issue was filed from this local workspace.

## Changes

- Add a focused regression for `PrivateMessage.send(client_a, User(client_b, ...), ...)`.
- Reuse `_validate_private_message_user_client(client, "recipient", recipient)` after send client validation and before login.
- Preserve successful `DashboardMessageAction` payload shape, recipient ID submission, subject/body submission, returned action-status validation, explicit non-`ok` status handling, and no-return successful sends.

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `PrivateMessage.send(client_a, User(client=client_b, ...), "Subject", "Body")` must raise `ValueError("recipient must belong to the client")` before login checks or AMC requests. |
| R2 | Existing malformed subject/body, malformed recipient shape, and malformed client diagnostics must keep their current precedence. |
| R3 | Valid same-client private-message sends must keep the same request payload shape and login-required behavior. |
| R4 | Existing returned action-status diagnostics, direct reads, inbox/sent-box acquisition, client accessors, and adjacent user/client workflows must remain unchanged. |
| R5 | The draft and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private messages, raw rollout paths, pushes, upstream Issues, or upstream PRs. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Cross-client send recipients fail at the public mutation boundary. | `TestPrivateMessage.test_send_rejects_recipient_from_different_client_before_login` failed RED because the mismatched recipient reached AMC/status handling, then passed GREEN after send called the recipient-client coherence validator. | Reaching `client.login_check()`, calling `client.amc_client.request(...)`, submitting a `to_user_id` from a different client context, or surfacing returned-status exceptions rejects this local completion claim. | `PrivateMessage.send(...)` | `src/wikidot/module/private_message.py`, `tests/unit/test_private_message.py` |
| R2 | Existing input-validation precedence remains stable. | Focused GREEN included malformed send client, non-`User` recipient, malformed recipient fields, and non-string text-input tests. | Moving malformed client, malformed recipient, or malformed text inputs behind login/request work rejects this local completion claim. | Send input preflight | `tests/unit/test_private_message.py` |
| R3 | Valid sends remain unchanged. | Focused GREEN included `test_send_requires_login` and `test_send_success`; full private-message coverage passed 135 tests. | Changing `DashboardMessageAction`, `event=send`, `to_user_id`, `subject`, `source`, or login-required behavior rejects this local completion claim. | Private-message send mutation | `tests/unit/test_private_message.py` |
| R4 | Adjacent workflows remain green. | Adjacent private-message/client/client-accessors/user coverage passed 253 tests; full unit coverage passed 2747 tests; full ruff, format check, mypy, pyright, and whitespace checks passed. | Regressing direct reads, inbox/sent wrappers, duplicate detail reuse, parser diagnostics, client accessors, user lookups, or action-status diagnostics rejects this local completion claim. | Private-message and adjacent workflows | `tests/unit` |
| R5 | No live auth material or private message content is needed to prove the behavior. | The regression uses synthetic `Client` and `User` objects only, and this draft contains no credentials, cookies, auth JSON, raw message bodies, private subjects, private recipient data, raw rollout paths, pushes, upstream Issues, or upstream PRs. | Using real account names, credentials, cookies, auth JSON, sandbox details, raw rollout paths, private message bodies, private subjects, private recipient names, pushes, upstream Issues, upstream PRs, or live Wikidot actions rejects this local completion claim. | Test and draft privacy | this draft |

## Testing

Implemented locally in commit `89e855d fix(private_message): validate send recipient client`.

- RED: `uv run pytest tests/unit/test_private_message.py::TestPrivateMessage::test_send_rejects_recipient_from_different_client_before_login -q` failed 1 test before the fix because the cross-client recipient reached AMC/status handling and raised `WikidotStatusCodeException`.
- GREEN regression: the same focused command passed 1 test.
- GREEN focused send coverage: `uv run pytest tests/unit/test_private_message.py::TestPrivateMessage::test_send_requires_login tests/unit/test_private_message.py::TestPrivateMessage::test_send_success tests/unit/test_private_message.py::TestPrivateMessage::test_send_rejects_malformed_client_before_login tests/unit/test_private_message.py::TestPrivateMessage::test_send_rejects_non_user_recipient_before_login tests/unit/test_private_message.py::TestPrivateMessage::test_send_rejects_malformed_user_recipient_before_login tests/unit/test_private_message.py::TestPrivateMessage::test_send_rejects_recipient_from_different_client_before_login tests/unit/test_private_message.py::TestPrivateMessage::test_send_rejects_non_string_text_inputs_before_login tests/unit/test_private_message.py::TestPrivateMessage::test_send_missing_action_status_includes_recipient_event_and_field_context tests/unit/test_private_message.py::TestPrivateMessage::test_send_explicit_non_ok_action_status_raises_status_exception -q` passed 16 tests.
- Private-message coverage: `uv run pytest tests/unit/test_private_message.py -q` passed 135 tests.
- Adjacent private-message/client/client-accessors/user coverage: `uv run pytest tests/unit/test_private_message.py tests/unit/test_client.py tests/unit/test_client_accessors.py tests/unit/test_user.py -q` passed 253 tests.
- `uv run pytest tests/unit -q` passed 2747 tests.
- `uv run ruff format src/wikidot/module/private_message.py tests/unit/test_private_message.py` left 2 files unchanged.
- `uv run ruff check src/wikidot/module/private_message.py tests/unit/test_private_message.py` passed.
- `uv run ruff check src tests` passed.
- `uv run ruff format --check src tests` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run pyright src tests` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `PrivateMessage.send(client_a, User(client=client_b, id=12345, name="test-user", ...), "Subject", "Body")` raises `ValueError("recipient must belong to the client")`.
- The cross-client recipient failure happens before `client.login_check()` or `client.amc_client.request(...)`.
- Existing malformed send text values still raise `ValueError("subject must be a string")` or `ValueError("body must be a string")`.
- Existing malformed send recipients still raise `ValueError("recipient must be a User")`, `ValueError("recipient.id must be an integer")`, or `ValueError("recipient.name must be a string")`.
- Existing malformed direct send clients still raise `ValueError("client must be a Client")`.
- Valid same-client sends still submit `DashboardMessageAction` with `event: "send"`, `to_user_id`, `subject`, and `source`.
- Existing missing-status and explicit non-`ok` action-status diagnostics remain unchanged.
- The new tests use unit-level synthetic values only and do not require live Wikidot, credentials, cookies, auth JSON, private message data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

`PrivateMessage.send(...)` is a direct mutation boundary. The request is submitted by one client while the recipient object supplies the `to_user_id` and diagnostic display name. Requiring the recipient to belong to the submitting client prevents generated fixtures, cached user objects, or mixed-client workflows from accidentally issuing a send under an incoherent object graph, without changing valid same-client sends or returned response handling.

## Local Evidence, Not For Upstream Paste

- The focused RED failure showed `PrivateMessage.send(client_a, User(client_b, ...), ...)` progressing into AMC/status handling instead of failing at the public input boundary.
- Existing local drafts covered private-message fetch retries, duplicate detail reduction, parser diagnostics, response-body diagnostics, send text validation, send recipient shape validation, send client validation, mailbox client validation, accessor client validation, record parent-client validation, and stored participant-client coherence, but did not cover direct send recipient/client coherence.
- This slice only validates direct send recipient/client coherence. It does not change private-message detail acquisition, message list acquisition, parser selectors, retry behavior, stored `PrivateMessage(...)` records, inbox/sent-box wrappers, live site behavior, authentication semantics for valid clients, send retry policy, or returned action-status policy.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, private message bodies, private message subjects, recipient names from real messages, and private site data out of upstream discussion.

## Additional Notes

The check intentionally compares client object identity rather than user IDs, usernames, account names, or authentication state. This matches the direct record coherence rule from Issue 613 and avoids network lookups, login checks, remote account checks, or ambiguous cross-client equivalence rules.
