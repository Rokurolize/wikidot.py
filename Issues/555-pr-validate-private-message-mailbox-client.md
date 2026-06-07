# PR Draft: Validate Private Message Mailbox Acquire Clients

## Summary

`PrivateMessageCollection.from_ids(client, message_ids)` already validates malformed non-empty direct detail-read clients, and `PrivateMessage.send(...)` validates direct send clients. One adjacent mailbox-list boundary still used the generic `login_required` decorator diagnostic: direct `PrivateMessageInbox.acquire(client)` and `PrivateMessageSentBox.acquire(client)` calls with malformed clients such as `None`, booleans, strings, dictionaries, or arbitrary objects raised `ValueError("Client is not found")` instead of the explicit private-message client diagnostic used by the surrounding public helpers.

This change validates the caller-provided mailbox acquire client in the shared factory before the decorated `_acquire(...)` call. Malformed inbox and sent-box acquire clients now raise `ValueError("client must be a Client")` before login checks, AMC list fetches, message-list parsing, or delegated detail reads. Valid inbox/sent-box acquisition, direct detail reads, direct sends, empty detail batches, retry behavior, parser diagnostics, and client private-message accessors remain unchanged.

## Outcome

Private-message inbox and sent-box list acquisition now report the same explicit client preflight as other private-message public helpers.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who call inbox or sent-box acquisition directly, use `client.private_message.inbox` / `sentbox`, or load mailbox inputs from generated local fixtures where malformed client objects should fail before login or request work.

## Current Evidence

Existing drafts [425-pr-validate-private-message-collection-initialization.md](425-pr-validate-private-message-collection-initialization.md), [451-pr-validate-private-message-id-field.md](451-pr-validate-private-message-id-field.md), [479-pr-validate-client-accessor-parent-clients.md](479-pr-validate-client-accessor-parent-clients.md), [546-pr-validate-private-message-read-client.md](546-pr-validate-private-message-read-client.md), and [547-pr-validate-private-message-send-client.md](547-pr-validate-private-message-send-client.md) establish private-message collection state, message IDs, accessor parents, direct detail-read clients, and direct send clients as active boundaries. This slice covers the remaining mailbox-list acquire wrappers, not direct detail reads, sends, or accessor construction.

No upstream issue was filed from this local workspace.

## Changes

- Validate `client` in `PrivateMessageCollection._factory_acquire(...)` before calling the decorated `_acquire(...)`.
- Add shared inbox/sent-box regressions for malformed direct `acquire(client=...)` inputs.
- Assert malformed acquire clients do not reach `_amc_request_with_retry(...)`.
- Preserve valid inbox/sent-box acquisition, direct detail reads, direct sends, parser diagnostics, retry behavior, and client accessor delegation.

## Type Of Change

- Input validation
- Public read-boundary diagnostic hardening
- Private-message mailbox setup hardening
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `PrivateMessageInbox.acquire(None)`, `True`, `"test-client"`, `{"username": "test-user"}`, and `object()` must raise `ValueError("client must be a Client")` before mailbox fetch work. |
| R2 | `PrivateMessageSentBox.acquire(...)` must reject the same malformed client values with the same diagnostic and before mailbox fetch work. |
| R3 | Existing `PrivateMessageCollection.from_ids(...)` client validation, ID validation, empty-batch behavior, and detail parsing must remain unchanged. |
| R4 | Existing valid inbox/sent-box acquisition, direct sends, client private-message accessors, retry behavior, response-body diagnostics, parser diagnostics, and adjacent user/site/client workflows must remain unchanged. |
| R5 | Private-message module tests, adjacent private-message/client/user/site tests, full unit, lint, format, mypy, pyright, and whitespace gates must pass before claiming this local implementation complete. |
| R6 | The draft and tests must not require live Wikidot actions, credentials, cookies, auth JSON, raw rollout paths, pushes, upstream Issues, or upstream PRs. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Malformed inbox acquire clients fail with the explicit private-message client diagnostic before fetch work. | `TestPrivateMessageMailboxAcquire.test_acquire_rejects_malformed_client_before_fetch` failed RED for 5 inbox cases with `ValueError("Client is not found")`, then passed GREEN after the shared factory preflight was added. | Reaching `_amc_request_with_retry`, relying on the generic decorator diagnostic, accepting client-like dictionaries, or leaking lower-level errors rejects this local completion claim. | `PrivateMessageInbox.acquire(...)` | `src/wikidot/module/private_message.py`, `tests/unit/test_private_message.py` |
| R2 | Malformed sent-box acquire clients fail with the same explicit diagnostic before fetch work. | The same focused test failed RED for 5 sent-box cases with `ValueError("Client is not found")`, then passed GREEN after validation was added. | Reaching `_amc_request_with_retry`, relying on the generic decorator diagnostic, accepting client-like dictionaries, or leaking lower-level errors rejects this local completion claim. | `PrivateMessageSentBox.acquire(...)` | `src/wikidot/module/private_message.py`, `tests/unit/test_private_message.py` |
| R3 | Direct detail-read behavior remains stable. | Existing `PrivateMessageCollection.from_ids(...)`, empty-batch, ID validation, response diagnostics, and detail parser tests passed inside the 127-test private-message module run. | Regressing empty-batch no-op behavior, duplicate ID ordering, detail parser diagnostics, no-message mapping, retry behavior, or message ID validation rejects this local completion claim. | Direct PM reads | `tests/unit/test_private_message.py` |
| R4 | Existing private-message and adjacent workflows remain stable. | Private-message module tests passed 127 tests, adjacent private-message/client/accessor/user/site tests passed 527 tests, and full unit passed 2646 tests. | Regressing valid inbox/sent-box acquisition, direct sends, client accessors, user/site workflows, parser diagnostics, response-body diagnostics, or retries rejects this local completion claim. | Private-message and adjacent workflows | `tests/unit` |
| R5 | Existing repository quality gates remain green. | Full ruff check and format check passed, full mypy passed with no issues in 87 source files, full pyright passed with 0 errors, 0 warnings, and 0 informations, and `git diff --check` passed. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |
| R6 | No live auth material or private state is needed to prove the behavior. | All regressions use synthetic malformed clients and patched mailbox fetch helpers; this draft contains no credentials, cookies, auth JSON, raw message bodies, private response bodies, or live site data. | Using real account names, credentials, cookies, auth JSON, sandbox details, raw rollout paths, pushes, upstream Issues, upstream PRs, live Wikidot actions, private messages, or private site data rejects this local completion claim. | Test and draft privacy | this draft |

## Testing

Implemented locally in commit `2862682 fix(private_message): validate mailbox acquire client`.

- RED mailbox acquire clients: `uv run pytest tests/unit/test_private_message.py::TestPrivateMessageMailboxAcquire::test_acquire_rejects_malformed_client_before_fetch -q` failed 10 tests before the fix because inbox and sent-box malformed clients raised the generic `ValueError("Client is not found")`.
- GREEN focused: the same focused command passed 10 tests.
- `uv run pytest tests/unit/test_private_message.py -q` passed 127 tests.
- `uv run pytest tests/unit/test_private_message.py tests/unit/test_client.py tests/unit/test_client_accessors.py tests/unit/test_user.py tests/unit/test_site.py -q` passed 527 tests.
- `uv run pytest tests/unit -q` passed 2646 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `PrivateMessageInbox.acquire(...)` rejects malformed clients with `ValueError("client must be a Client")` before login checks or mailbox-list fetch work.
- `PrivateMessageSentBox.acquire(...)` rejects the same malformed clients with the same diagnostic and before fetch work.
- Direct PM detail reads, direct sends, collection construction, message ID validation, retry behavior, parser diagnostics, and client accessors remain unchanged.
- The new tests use unit-level synthetic values only and do not require live Wikidot, credentials, cookies, auth JSON, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Risks And Mitigations

- Risk: This could be mistaken for direct detail-read client validation. Mitigation: Issue 546 still covers `PrivateMessageCollection.from_ids(...)`; this slice covers mailbox list acquisition wrappers.
- Risk: This could be mistaken for accessor parent validation. Mitigation: Issue 479 covers `ClientPrivateMessageAccessor(client=...)`; this slice covers `PrivateMessageInbox.acquire(...)` and `PrivateMessageSentBox.acquire(...)`.
- Risk: Valid mailbox acquisition could accidentally bypass login-required behavior. Mitigation: valid private-message module and adjacent client/accessor tests remain green.

## Dependencies

- Existing private-message client validator remains the shared source for `client must be a Client`.
- Existing `login_required` behavior remains responsible for valid clients that are not logged in.
- Existing direct detail-read validation remains responsible for `PrivateMessageCollection.from_ids(...)`.

## Open Questions

None for this local slice.

## Upstream-Safe Motivation

Inbox and sent-box acquisition are practical browser-free mailbox entry points. Giving malformed mailbox clients the same explicit diagnostic as direct PM reads and sends makes generated callers, fixtures, and config adapters easier to diagnose without changing live Wikidot behavior, valid login checks, request shape, retries, parsing, or accessor workflows.

## Local Evidence, Not For Upstream Paste

- The focused RED failures showed inbox and sent-box acquire wrappers reaching the generic login decorator and raising `Client is not found` instead of the private-message client diagnostic.
- This slice only validates mailbox acquire clients. It does not change private-message detail parsing, inbox/sent-box selectors, response-body diagnostics, message ID validation, retry controls, collection initialization, record field validation, send behavior, live site behavior, or authentication semantics for valid clients.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, private response data, private-message content, and live Wikidot account details out of upstream discussion.
