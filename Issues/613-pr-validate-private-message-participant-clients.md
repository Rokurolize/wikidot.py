# PR Draft: Validate PrivateMessage Participant Clients

## Summary

`PrivateMessage` records carry a parent `Client`, a `sender`, and a `recipient`. Existing private-message slices validate direct read clients, direct send clients, mailbox acquire clients, accessor parent clients, record parent clients, message IDs, collection entries, retry controls, parser diagnostics, response bodies, stored sender/recipient types, text fields, and timestamps. One constructor coherence gap remained after Issue 612: direct `PrivateMessage(...)` construction could combine `client=client_a` with `sender=User(client=client_b, ...)` or `recipient=User(client=client_b, ...)`, producing a PM record whose participant user came from a different client context than the record parent.

This change validates `PrivateMessage.sender.client` and `PrivateMessage.recipient.client` against `PrivateMessage.client` during `PrivateMessage.__post_init__`, after the existing parent-client and participant type checks and before subject/body/timestamp validation. Mismatches raise `ValueError("sender must belong to the client")` or `ValueError("recipient must belong to the client")`. Parser-created messages remain aligned because `PrivateMessageCollection.from_ids(...)` validates the parent client and parses both header users with `user_parser(client, user_elem)`. Existing malformed field diagnostics, valid direct rows, direct reads, inbox/sent-box acquisition, duplicate detail reuse, `from_id(...)`, send behavior, collection behavior, and adjacent client/user workflows remain unchanged.

## Outcome

Private-message records cannot store sender or recipient users from a different client context than the record parent.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use browser-free private-message detail reads, inbox/sent-box acquisition, PM audit ledgers, migration checks, generated fixtures, `Client.private_message` accessors, or direct `PrivateMessage(...)` construction in local tests.

## Current Evidence

Local rollout-backed drafts repeatedly identify private-message reads and sends as practical workflow surfaces. Existing drafts [037-pr-retry-private-message-fetches.md](037-pr-retry-private-message-fetches.md), [054-pr-deduplicate-private-message-detail-fetches.md](054-pr-deduplicate-private-message-detail-fetches.md), [067-pr-deduplicate-direct-private-message-fetches.md](067-pr-deduplicate-direct-private-message-fetches.md), [073-pr-reuse-private-message-detail-parsing.md](073-pr-reuse-private-message-detail-parsing.md), [077-pr-skip-empty-private-message-fetch-batches.md](077-pr-skip-empty-private-message-fetch-batches.md), [206-pr-private-message-detail-response-body-context.md](206-pr-private-message-detail-response-body-context.md), [207-pr-private-message-list-response-body-context.md](207-pr-private-message-list-response-body-context.md), [288-pr-private-message-detail-user-context.md](288-pr-private-message-detail-user-context.md), [355-pr-validate-private-message-send-text-inputs.md](355-pr-validate-private-message-send-text-inputs.md), [360-pr-validate-private-message-send-recipients.md](360-pr-validate-private-message-send-recipients.md), [361-pr-validate-private-message-message-id-inputs.md](361-pr-validate-private-message-message-id-inputs.md), [397-pr-validate-private-message-retry-controls.md](397-pr-validate-private-message-retry-controls.md), [425-pr-validate-private-message-collection-initialization.md](425-pr-validate-private-message-collection-initialization.md), [451-pr-validate-private-message-id-field.md](451-pr-validate-private-message-id-field.md), [479-pr-validate-client-accessor-parent-clients.md](479-pr-validate-client-accessor-parent-clients.md), [498-pr-validate-private-message-record-fields.md](498-pr-validate-private-message-record-fields.md), [546-pr-validate-private-message-read-client.md](546-pr-validate-private-message-read-client.md), [547-pr-validate-private-message-send-client.md](547-pr-validate-private-message-send-client.md), [555-pr-validate-private-message-mailbox-client.md](555-pr-validate-private-message-mailbox-client.md), and [612-pr-validate-private-message-record-client.md](612-pr-validate-private-message-record-client.md) establish private-message acquisition, parsing, mutation, collection state, record-state validation, and parent-client validation as active operational boundaries.

The parser path already constructs sender and recipient users with the message record's parent client: `PrivateMessageCollection.from_ids(...)` calls `_parse_message_user(client, ..., "sender")` and `_parse_message_user(client, ..., "recipient")`, and that helper calls `user_parser(client, user_element)`. The new rule brings direct constructor behavior in line with that parser invariant.

## Related Issue / Non-Duplicate Analysis

This is not a duplicate of Issue 498. Issue 498 validates that `sender` and `recipient` are `AbstractUser` instances; it does not validate the relationship between a valid participant object and the record parent client.

This is not a duplicate of Issue 612. Issue 612 validates that `PrivateMessage.client` itself is a `Client`; it explicitly leaves participant/client coherence to this separate slice.

This is not a duplicate of Issue 288. Issue 288 validates malformed generated sender/recipient user markup at the parser boundary, not direct record-state coherence after parser output has become user objects.

This is not a duplicate of Issues 546, 547, or 555. Those slices validate caller-provided clients for direct detail reads, direct sends, and inbox/sent-box acquisition. This slice validates stored participant users at `PrivateMessage(...)` construction.

This is not a duplicate of Issue 360. Issue 360 validates direct `PrivateMessage.send(...)` recipient input shape before mutation work. This slice validates stored sender/recipient coherence on message records and does not change send recipient behavior.

No upstream issue was filed from this local workspace.

## Changes

- Add `PrivateMessage` participant-client coherence validation.
- Reject direct rows where `sender.client is not client` with `ValueError("sender must belong to the client")`.
- Reject direct rows where `recipient.client is not client` with `ValueError("recipient must belong to the client")`.
- Preserve existing validation order for malformed `id`, malformed parent `client`, malformed `sender`, and malformed `recipient` diagnostics before coherence checks.
- Preserve side-effect-free construction: the new checks compare object identity only and do not perform login checks, AMC requests, user lookups, sends, coercion, or auth-state mutation.

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `PrivateMessage(client=client_a, sender=User(client=client_b, ...), ...)` must reject the mismatched sender client with `ValueError("sender must belong to the client")`. |
| R2 | `PrivateMessage(client=client_a, recipient=User(client=client_b, ...), ...)` must reject the mismatched recipient client with `ValueError("recipient must belong to the client")`. |
| R3 | Valid direct `PrivateMessage(...)` rows where both participants use the parent client and parser-created detail rows must remain valid. |
| R4 | Existing malformed `id`, parent `client`, participant type, subject, body, and `created_at` diagnostics must remain unchanged. |
| R5 | Existing direct reads, empty reads, inbox/sent-box acquisition, duplicate detail reuse, `from_id(...)`, send behavior, client accessors, and adjacent user/client workflows must remain unchanged. |
| R6 | The draft and tests must not require live Wikidot actions, credentials, cookies, auth JSON, raw rollout paths, pushes, upstream Issues, or upstream PRs. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Constructor sender/client mismatches fail at the public dataclass boundary. | `TestPrivateMessage.test_init_rejects_message_users_from_different_client` failed RED for sender with `DID NOT RAISE`, then passed GREEN after `PrivateMessage.__post_init__` called the participant-client preflight. | Accepting a valid `User` object from another client context, emitting a message row whose parent client and sender client disagree, or deferring the mismatch to later code rejects this local completion claim. | `PrivateMessage` constructor | `src/wikidot/module/private_message.py`, `tests/unit/test_private_message.py` |
| R2 | Constructor recipient/client mismatches fail at the public dataclass boundary. | The same focused test failed RED for recipient with `DID NOT RAISE`, then passed GREEN with `ValueError("recipient must belong to the client")`. | Accepting a valid `User` object from another client context, emitting a message row whose parent client and recipient client disagree, or deferring the mismatch to later code rejects this local completion claim. | `PrivateMessage` constructor | `src/wikidot/module/private_message.py`, `tests/unit/test_private_message.py` |
| R3 | Existing valid direct and parser-created messages stay green. | `tests/unit/test_private_message.py` passed 134 tests, and adjacent private-message/client/accessor/user coverage passed 252 tests. | Rejecting same-client participants, replacing participant objects, coercing users, breaking parsed message output, or requiring live authentication rejects this local completion claim. | Private-message records | `tests/unit/test_private_message.py` |
| R4 | Existing diagnostics stay stable. | Full private-message coverage passed existing malformed message ID, parent-client, sender, recipient, subject, body, `created_at`, read-client, send-client, and mailbox-client tests. | Changing existing `ValueError` messages, accepting previously rejected malformed values, or validating coherence before malformed field checks rejects this local completion claim. | Private-message validation order | `tests/unit/test_private_message.py` |
| R5 | Existing adjacent workflows remain green. | Full unit coverage passed 2746 tests; full ruff, format check, mypy, pyright, and whitespace checks passed. | Regressing direct reads, inbox/sent wrappers, duplicate message ID reuse, parser diagnostics, `from_id(...)`, send payload construction, client accessors, or user lookup workflows rejects this local completion claim. | Private-message and adjacent workflows | `tests/unit` |
| R6 | No live auth material or private message content is needed to prove the behavior. | The regression uses synthetic `Client` and `User` objects only, and this draft contains no credentials, cookies, auth JSON, raw message bodies, private subjects, raw rollout paths, pushes, upstream Issues, or upstream PRs. | Using real account names, credentials, cookies, auth JSON, sandbox details, raw rollout paths, private message bodies, private subjects, pushes, upstream Issues, upstream PRs, or live Wikidot actions rejects this local completion claim. | Test and draft privacy | this draft |

## Testing

Implemented locally in commit `ed80a82 fix(private_message): validate participant clients`.

- RED: `uv run pytest tests/unit/test_private_message.py::TestPrivateMessage::test_init_rejects_message_users_from_different_client -q` failed 2 tests before the fix with `DID NOT RAISE`.
- GREEN regression: the same focused command passed 2 tests.
- Private-message coverage: `uv run pytest tests/unit/test_private_message.py -q` passed 134 tests.
- Adjacent private-message/client/client-accessors/user coverage: `uv run pytest tests/unit/test_private_message.py tests/unit/test_client.py tests/unit/test_client_accessors.py tests/unit/test_user.py -q` passed 252 tests.
- `uv run pytest tests/unit -q` passed 2746 tests.
- `uv run ruff format src/wikidot/module/private_message.py tests/unit/test_private_message.py` left 2 files unchanged.
- `uv run ruff check src/wikidot/module/private_message.py tests/unit/test_private_message.py` passed.
- `uv run ruff check src tests` passed.
- `uv run ruff format --check src tests` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run pyright src tests` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `PrivateMessage(client=client_a, sender=User(client=client_b, ...), recipient=same_client_user, ...)` raises `ValueError("sender must belong to the client")`.
- `PrivateMessage(client=client_a, sender=same_client_user, recipient=User(client=client_b, ...), ...)` raises `ValueError("recipient must belong to the client")`.
- Valid direct rows where `sender.client is client` and `recipient.client is client` remain valid.
- Existing malformed `sender` and `recipient` values still raise field-specific `AbstractUser` diagnostics.
- Existing malformed `id`, parent `client`, `subject`, `body`, and `created_at` diagnostics remain unchanged.
- Existing parser-created message records still produce valid `PrivateMessage` rows.
- Existing direct reads, inbox/sent-box acquisition, duplicate detail reuse, `from_id(...)`, send behavior, collection behavior, client accessors, and adjacent user/client workflows remain green.
- The new tests use unit-level synthetic values only and do not require live Wikidot, credentials, cookies, auth JSON, private message data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

`PrivateMessage` is the durable record shape behind browser-free private-message detail reads, inbox/sent-box acquisition, generated PM ledgers, migration checks, and local fixtures. Detail parsing already creates both participant users with the same validated parent client. Constructor coherence validation keeps direct fixtures and serialized rows from mixing participant client contexts while preserving normal PM read, parse, collection, and send behavior.

## Local Evidence, Not For Upstream Paste

- The focused RED failure showed direct `PrivateMessage(client=client_a, sender=User(client=client_b, ...), ...)` and direct `PrivateMessage(client=client_a, recipient=User(client=client_b, ...), ...)` construction silently accepted contradictory records.
- Existing local drafts covered private-message fetch retries, duplicate detail reduction, parser diagnostics, response-body diagnostics, send input validation, message ID validation, collection initialization, retry controls, direct read client validation, send client validation, mailbox client validation, accessor client validation, parent record-client validation, and stored participant type validation, but did not cover direct participant/client coherence at `PrivateMessage(...)` construction.
- This slice only validates constructor-time sender/recipient client coherence. It does not change message detail request construction, message list acquisition, parser selectors, user parser semantics, retry behavior, `PrivateMessageCollection.from_ids(...)`, `PrivateMessage.send(...)`, inbox/sent-box wrappers, live site behavior, authentication semantics, or request helper behavior.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, private message bodies, private message subjects, recipient names from real messages, and private site data out of upstream discussion.

## Additional Notes

The check intentionally compares client object identity rather than user IDs, usernames, account names, or authentication state. The parser path and retained object graph preserve client identity, and identity comparison avoids network lookups, login checks, remote account checks, or ambiguous cross-client equivalence rules.
