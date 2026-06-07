# PR Draft: Validate PrivateMessage Record Client

## Summary

`PrivateMessage` records carry a parent `Client`, sender, recipient, subject, body, and creation timestamp. They are produced by browser-free private-message detail reads, inbox/sent-box acquisition, `Client.private_message` accessors, duplicate detail reuse, generated PM ledgers, local fixtures, and serialized or rehydrated record state. Existing private-message slices validate direct read clients, direct send clients, mailbox acquire clients, accessor parent clients, message IDs, collection entries, retry controls, parser diagnostics, response bodies, stored sender/recipient types, text fields, and timestamps. One direct record-state gap remained: `PrivateMessage(client=...)` accepted malformed parent clients such as `None`, booleans, strings, dictionaries, or arbitrary objects when every other field was valid.

This change validates `PrivateMessage.client` during `PrivateMessage.__post_init__` with the existing `_validate_private_message_client(...)` helper. Malformed record parents now raise `ValueError("client must be a Client")` before sender, recipient, text, timestamp, or later workflow code can operate on a record with invalid parent state. Valid parser-created messages, direct fixture rows, `from_id(...)`, `from_ids(...)`, inbox/sent-box acquisition, duplicate detail reuse, send behavior, and adjacent client/user workflows remain unchanged.

## Outcome

Private-message records cannot store a malformed parent client.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use browser-free private-message detail reads, inbox/sent-box acquisition, PM audit ledgers, migration checks, generated fixtures, `Client.private_message` accessors, or direct `PrivateMessage(...)` construction in local tests.

## Current Evidence

Local rollout-backed drafts repeatedly identify private-message reads and sends as practical workflow surfaces. Existing drafts [037-pr-retry-private-message-fetches.md](037-pr-retry-private-message-fetches.md), [054-pr-deduplicate-private-message-detail-fetches.md](054-pr-deduplicate-private-message-detail-fetches.md), [067-pr-deduplicate-direct-private-message-fetches.md](067-pr-deduplicate-direct-private-message-fetches.md), [073-pr-reuse-private-message-detail-parsing.md](073-pr-reuse-private-message-detail-parsing.md), [077-pr-skip-empty-private-message-fetch-batches.md](077-pr-skip-empty-private-message-fetch-batches.md), [206-pr-private-message-detail-response-body-context.md](206-pr-private-message-detail-response-body-context.md), [207-pr-private-message-list-response-body-context.md](207-pr-private-message-list-response-body-context.md), [288-pr-private-message-detail-user-context.md](288-pr-private-message-detail-user-context.md), [355-pr-validate-private-message-send-text-inputs.md](355-pr-validate-private-message-send-text-inputs.md), [360-pr-validate-private-message-send-recipients.md](360-pr-validate-private-message-send-recipients.md), [361-pr-validate-private-message-message-id-inputs.md](361-pr-validate-private-message-message-id-inputs.md), [397-pr-validate-private-message-retry-controls.md](397-pr-validate-private-message-retry-controls.md), [425-pr-validate-private-message-collection-initialization.md](425-pr-validate-private-message-collection-initialization.md), [451-pr-validate-private-message-id-field.md](451-pr-validate-private-message-id-field.md), [479-pr-validate-client-accessor-parent-clients.md](479-pr-validate-client-accessor-parent-clients.md), [498-pr-validate-private-message-record-fields.md](498-pr-validate-private-message-record-fields.md), [546-pr-validate-private-message-read-client.md](546-pr-validate-private-message-read-client.md), [547-pr-validate-private-message-send-client.md](547-pr-validate-private-message-send-client.md), and [555-pr-validate-private-message-mailbox-client.md](555-pr-validate-private-message-mailbox-client.md) establish private-message acquisition, parsing, mutation, collection state, and parent-client validation as active operational boundaries.

Parser-created private-message records already receive the same `Client` object that was validated by `PrivateMessageCollection.from_ids(...)`. The new check brings direct constructor behavior in line with that read-path invariant.

## Related Issue / Non-Duplicate Analysis

This is not a duplicate of Issue 498. Issue 498 validates stored `sender`, `recipient`, `subject`, `body`, and `created_at` fields; it does not validate the separate parent `client` field.

This is not a duplicate of Issues 546, 547, or 555. Those slices validate caller-provided clients for direct detail reads, direct sends, and inbox/sent-box acquisition. This slice validates stored record state at `PrivateMessage(...)` construction.

This is not a duplicate of Issue 479. Issue 479 validates `ClientPrivateMessageAccessor(client=...)` and adjacent accessor parents. This slice validates the `PrivateMessage` dataclass parent.

This is not a duplicate of Issue 288. Issue 288 validates malformed generated sender/recipient user markup at the parser boundary, not the direct record parent client.

No upstream issue was filed from this local workspace.

## Changes

- Validate `PrivateMessage.client` during `PrivateMessage.__post_init__`.
- Reuse the existing private-message client diagnostic: `ValueError("client must be a Client")`.
- Preserve existing message-ID validation before parent-client validation.
- Preserve existing sender, recipient, subject, body, and `created_at` validation behavior.
- Preserve side-effect-free construction: the new check performs only an `isinstance` check and does not login, issue AMC requests, fetch message details, send messages, coerce clients, or mutate auth state.

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `PrivateMessage(client=None)`, booleans, strings, dictionaries, and arbitrary objects must raise `ValueError("client must be a Client")` when every other field is valid. |
| R2 | Valid parser-created and direct `PrivateMessage(...)` records with a real `Client` parent must remain valid. |
| R3 | Existing message ID, sender, recipient, subject, body, and `created_at` diagnostics must remain unchanged. |
| R4 | Existing direct reads, empty reads, inbox/sent-box acquisition, duplicate detail reuse, `from_id(...)`, send behavior, client accessors, and adjacent user/client workflows must remain unchanged. |
| R5 | The draft and tests must not require live Wikidot actions, credentials, cookies, auth JSON, raw rollout paths, pushes, upstream Issues, or upstream PRs. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Constructor parent-client mismatches fail at the public dataclass boundary. | `TestPrivateMessage.test_init_rejects_malformed_client` failed RED for 5 malformed clients with `DID NOT RAISE`, then passed GREEN after `PrivateMessage.__post_init__` called `_validate_private_message_client(...)`. | Accepting malformed parent clients, deferring failures to later reads/sends, or leaking raw attribute errors rejects this local completion claim. | `PrivateMessage` constructor | `src/wikidot/module/private_message.py`, `tests/unit/test_private_message.py` |
| R2 | Valid direct and parser-created messages stay green. | `tests/unit/test_private_message.py` passed 132 tests, and adjacent private-message/client/accessor/user coverage passed 250 tests. | Rejecting valid `Client` parents, changing parsed message output, or breaking fixture-created messages rejects this local completion claim. | Private-message records | `tests/unit/test_private_message.py` |
| R3 | Existing diagnostics stay stable. | Full private-message coverage passed existing malformed message ID, sender, recipient, subject, body, `created_at`, read-client, send-client, and mailbox-client tests. | Changing existing `ValueError` messages, accepting previously rejected malformed values, or moving malformed ID checks behind client validation rejects this local completion claim. | Private-message validation order | `tests/unit/test_private_message.py` |
| R4 | Existing adjacent workflows remain green. | Full unit coverage passed 2744 tests; full ruff, format check, mypy, pyright, and whitespace checks passed. | Regressing direct reads, inbox/sent wrappers, duplicate message ID reuse, parser diagnostics, `from_id(...)`, send payload construction, client accessors, or user lookup workflows rejects this local completion claim. | Private-message and adjacent workflows | `tests/unit` |
| R5 | No live auth material or private message content is needed to prove the behavior. | The regression uses synthetic `Client` and `User` objects only, and this draft contains no credentials, cookies, auth JSON, raw message bodies, private subjects, raw rollout paths, pushes, upstream Issues, or upstream PRs. | Using real account names, credentials, cookies, auth JSON, sandbox details, raw rollout paths, private message bodies, private subjects, pushes, upstream Issues, upstream PRs, or live Wikidot actions rejects this local completion claim. | Test and draft privacy | this draft |

## Testing

Implemented locally in commit `0a99011 fix(private_message): validate record client`.

- RED: `uv run pytest tests/unit/test_private_message.py::TestPrivateMessage::test_init_rejects_malformed_client -q` failed 5 tests before the fix with `DID NOT RAISE`.
- GREEN regression: the same focused command passed 5 tests.
- Private-message coverage: `uv run pytest tests/unit/test_private_message.py -q` passed 132 tests.
- Adjacent private-message/client/client-accessors/user coverage: `uv run pytest tests/unit/test_private_message.py tests/unit/test_client.py tests/unit/test_client_accessors.py tests/unit/test_user.py -q` passed 250 tests.
- `uv run pytest tests/unit -q` passed 2744 tests.
- `uv run ruff format src/wikidot/module/private_message.py tests/unit/test_private_message.py` left 2 files unchanged.
- `uv run ruff check src/wikidot/module/private_message.py tests/unit/test_private_message.py` passed.
- `uv run ruff check src tests` passed.
- `uv run ruff format --check src tests` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run pyright src tests` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `PrivateMessage(client=None, id=1, sender=valid_user, recipient=valid_user, subject="...", body="...", created_at=datetime(...))` raises `ValueError("client must be a Client")`.
- The same diagnostic applies to boolean, string, dictionary, and arbitrary-object parent clients.
- Existing malformed `id` inputs still raise `ValueError("message_id must be an integer")`.
- Existing malformed `sender` and `recipient` values still raise field-specific `AbstractUser` diagnostics.
- Existing malformed `subject`, `body`, and `created_at` diagnostics remain unchanged.
- Existing valid parser-created messages, direct fixtures, direct reads, inbox/sent-box acquisition, duplicate detail reuse, `from_id(...)`, send behavior, and client/user accessors remain green.
- The new tests use unit-level synthetic values only and do not require live Wikidot, credentials, cookies, auth JSON, private message data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

`PrivateMessage` is the durable record shape behind browser-free private-message detail reads, inbox/sent-box acquisition, generated PM ledgers, migration checks, and local fixtures. Read paths already validate their parent client before constructing records. Direct constructor validation keeps malformed parent state out of local records while preserving parser behavior, read behavior, send behavior, and message-field diagnostics.

## Local Evidence, Not For Upstream Paste

- The focused RED failure showed direct `PrivateMessage(client=...)` construction silently accepted malformed parent clients when every other field was valid.
- Existing local drafts covered private-message fetch retries, duplicate detail reduction, parser diagnostics, response-body diagnostics, send input validation, message ID validation, collection initialization, retry controls, direct read client validation, send client validation, mailbox client validation, accessor client validation, and stored non-client record fields, but did not cover the direct `PrivateMessage.client` dataclass field.
- This slice only validates constructor-time parent-client type. It does not change message detail request construction, message list acquisition, parser selectors, user parser semantics, retry behavior, `PrivateMessageCollection.from_ids(...)`, `PrivateMessage.send(...)`, inbox/sent-box wrappers, live site behavior, authentication semantics, or request helper behavior.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, private message bodies, private message subjects, recipient names from real messages, and private site data out of upstream discussion.

## Additional Notes

This intentionally does not yet validate that stored `sender.client` and `recipient.client` match `PrivateMessage.client`; that participant-client coherence is a separate adjacent candidate because it depends on valid parent-client state and distinct acceptance criteria.
