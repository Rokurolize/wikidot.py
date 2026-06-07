# PR Draft: Validate Private Message Direct Read Client Input

## Summary

`PrivateMessageCollection.from_ids(client, message_ids)` is the direct browser-free private-message detail read boundary behind `PrivateMessage.from_id(...)`, inbox/sent-box wrappers, and client private-message accessors. Earlier local slices validated message-ID inputs, retry controls, response-body diagnostics, parser diagnostics, collection initialization, message record fields, send recipients/text, and client accessor parent state. One adjacent public read-input gap remained: direct non-empty calls such as `PrivateMessageCollection.from_ids(None, [1])`, booleans, strings, dictionaries, or arbitrary objects reached `client.login_check()` and leaked raw `AttributeError`.

This change validates the caller-provided `client` object after message-ID validation and after the valid empty-batch shortcut, but before login checks, AMC request construction, retry handling, or detail parsing. Malformed direct non-empty client arguments now raise `ValueError("client must be a Client")` deterministically, while valid empty reads still return an empty collection without requiring login or client state.

## Outcome

Direct private-message detail callers now get deterministic client validation before authenticated read work instead of incidental attribute errors from malformed client-like values.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who call private-message detail reads directly, wrap them in generated ledgers, or rehydrate message IDs from local state where a malformed client fixture should fail before login and request work.

## Current Evidence

Local rollout-backed drafts repeatedly identify private-message reads as practical workflow surfaces. Existing drafts [037-pr-retry-private-message-fetches.md](037-pr-retry-private-message-fetches.md), [073-pr-reuse-private-message-detail-parsing.md](073-pr-reuse-private-message-detail-parsing.md), [077-pr-skip-empty-private-message-fetch-batches.md](077-pr-skip-empty-private-message-fetch-batches.md), [106-pr-preserve-private-message-body-spacing.md](106-pr-preserve-private-message-body-spacing.md), [119-pr-preserve-private-message-subject-spacing.md](119-pr-preserve-private-message-subject-spacing.md), [178-pr-private-message-list-fetch-failure-context.md](178-pr-private-message-list-fetch-failure-context.md), [188-pr-private-message-detail-parse-context.md](188-pr-private-message-detail-parse-context.md), [206-pr-private-message-detail-response-body-context.md](206-pr-private-message-detail-response-body-context.md), [207-pr-private-message-list-response-body-context.md](207-pr-private-message-list-response-body-context.md), [272-pr-private-message-detail-timestamp-context.md](272-pr-private-message-detail-timestamp-context.md), [273-pr-private-message-detail-subject-body-context.md](273-pr-private-message-detail-subject-body-context.md), [287-pr-private-message-detail-timestamp-value-context.md](287-pr-private-message-detail-timestamp-value-context.md), [288-pr-private-message-detail-user-context.md](288-pr-private-message-detail-user-context.md), [321-pr-private-message-response-body-type-context.md](321-pr-private-message-response-body-type-context.md), [361-pr-validate-private-message-message-id-inputs.md](361-pr-validate-private-message-message-id-inputs.md), [397-pr-validate-private-message-retry-controls.md](397-pr-validate-private-message-retry-controls.md), [425-pr-validate-private-message-collection-initialization.md](425-pr-validate-private-message-collection-initialization.md), [451-pr-validate-private-message-id-field.md](451-pr-validate-private-message-id-field.md), and [479-pr-validate-client-accessor-parent-clients.md](479-pr-validate-client-accessor-parent-clients.md) establish private-message detail reads, list reads, parser diagnostics, retry behavior, ID preflight, collection state, message record state, and accessor parent state as active operational boundaries.

This is not a duplicate of Issue 361. Issue 361 validates direct private-message `message_ids` and `message_id` inputs before login or AMC work. This slice validates the separate caller-provided `client` object for non-empty direct detail reads after valid ID preflight.

This is not a duplicate of Issue 397. Issue 397 validates retry config values read from a valid client's AMC config. This slice validates that direct private-message reads have a real `Client` before they can read login or AMC state.

This is not a duplicate of Issue 425 or Issue 451. Those slices validate collection initialization and stored private-message ID record fields after message objects exist. This slice validates the parent client argument before direct detail acquisition.

This is not a duplicate of Issue 479. Issue 479 validates `ClientPrivateMessageAccessor(client=...)` construction. This slice covers direct calls to `PrivateMessageCollection.from_ids(...)`, including wrappers that delegate through that direct read helper.

No upstream issue was filed from this local workspace.

## Changes

- Add a focused regression for malformed non-empty direct `PrivateMessageCollection.from_ids(client=...)` inputs.
- Add `_validate_private_message_client(...)` with the same public diagnostic shape used by client accessor validation.
- Preserve the existing empty valid message-ID batch shortcut before client validation.
- Preserve ID validation ordering, login-required behavior for valid clients, retry behavior, detail parsing, inbox/sent-box wrappers, `PrivateMessage.from_id(...)`, and adjacent client/user/site workflows.

## Type Of Change

- Input validation
- Public read-boundary hardening
- Private-message detail acquisition preflight
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `PrivateMessageCollection.from_ids(None, [1])`, `True`, `"test-client"`, `{"username": "test-user"}`, and `object()` must raise `ValueError("client must be a Client")` before login or AMC request work. |
| R2 | Valid empty direct message-ID batches must still return an empty `PrivateMessageCollection` without requiring login, client validation, or AMC request work. |
| R3 | Existing message-ID validation must remain earlier than client validation, and valid direct detail reads, wrappers, retry behavior, parser diagnostics, and `PrivateMessage.from_id(...)` must remain unchanged. |
| R4 | Private-message, adjacent client/user/site, full unit tests, lint, format, mypy, pyright, and whitespace gates must pass before claiming this local implementation complete. |
| R5 | The draft and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private messages, raw rollout paths, pushes, upstream Issues, or upstream PRs. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Malformed non-empty private-message direct read clients fail at the public read boundary. | `TestPrivateMessageCollection.test_from_ids_rejects_malformed_client_before_login` failed RED for all 5 malformed values with raw `AttributeError`, then passed GREEN after validation was added. | Reaching `client.login_check()`, accepting client-like dictionaries, building requests, or leaking raw attribute errors rejects this local completion claim. | `PrivateMessageCollection.from_ids(...)` | `src/wikidot/module/private_message.py`, `tests/unit/test_private_message.py` |
| R2 | Empty valid direct message-ID batches remain a no-login/no-fetch path. | Focused GREEN included `test_from_ids_empty_input_skips_login_and_fetch`. | Requiring a valid client, calling login, or issuing AMC requests for `[]` rejects this local completion claim. | Empty direct detail reads | `tests/unit/test_private_message.py` |
| R3 | Existing private-message direct read behavior remains stable. | Focused GREEN included non-list ID validation, non-integer ID-entry validation, successful direct read, and `PrivateMessage.from_id(...)`; the full private-message file passed 112 tests. | Changing ID validation messages, valid read output, wrapper delegation, retry behavior, parser output, or direct single-message delegation rejects this local completion claim. | Private-message direct reads | `tests/unit/test_private_message.py` |
| R4 | Existing repository quality gates remain green. | Adjacent client/accessor/user/site tests passed 377 tests, full unit tests passed 2588 tests, full ruff check and format check passed, full mypy passed with no issues in 87 source files, full pyright passed with 0 errors, 0 warnings, and 0 informations, and `git diff --check` passed. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |
| R5 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level synthetic state; this draft contains no credentials, cookies, auth JSON, raw private-message bodies, live account data, or live site data. | Using real account names, credentials, cookies, auth JSON, sandbox details, raw rollout paths, pushes, upstream Issues, upstream PRs, live Wikidot actions, raw private-message HTML, message text, usernames from private accounts, or private site data rejects this local completion claim. | Test and draft privacy | this draft |

## Testing

Implemented locally in commit `56c78dd fix(private_message): validate direct read client`.

- RED: `uv run pytest tests/unit/test_private_message.py::TestPrivateMessageCollection::test_from_ids_rejects_malformed_client_before_login -q` failed 5 tests before the fix because malformed clients reached `client.login_check()` and leaked raw `AttributeError`.
- GREEN focused: `uv run pytest tests/unit/test_private_message.py::TestPrivateMessageCollection::test_from_ids_rejects_malformed_client_before_login tests/unit/test_private_message.py::TestPrivateMessageCollection::test_from_ids_empty_input_skips_login_and_fetch tests/unit/test_private_message.py::TestPrivateMessageCollection::test_from_ids_rejects_non_list_message_ids_before_login tests/unit/test_private_message.py::TestPrivateMessageCollection::test_from_ids_rejects_non_integer_message_id_entries_before_login tests/unit/test_private_message.py::TestPrivateMessageCollection::test_from_ids_success tests/unit/test_private_message.py::TestPrivateMessage::test_from_id -q` passed 13 tests.
- `uv run pytest tests/unit/test_private_message.py -q` passed 112 tests.
- `uv run pytest tests/unit/test_client.py tests/unit/test_client_accessors.py tests/unit/test_user.py tests/unit/test_site.py -q` passed 377 tests.
- `uv run pytest tests/unit -q` passed 2588 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `uv run mypy .` passed with no issues in 87 source files.
- `uv run pyright .` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- Malformed non-empty direct `PrivateMessageCollection.from_ids(client=...)` inputs raise `ValueError("client must be a Client")`.
- Empty valid direct message-ID batches remain a no-login/no-fetch path.
- Existing ID validation, valid direct detail reads, retry behavior, parser diagnostics, inbox/sent-box wrapper delegation, and `PrivateMessage.from_id(...)` stay unchanged.
- Adjacent client, accessor, user, and site workflows stay green.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private messages, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Risks And Mitigations

- Risk: Client validation could accidentally disturb the established empty-batch no-login contract. Mitigation: validation runs only after the empty `message_ids` shortcut, and focused GREEN includes that behavior.
- Risk: The direct-read diagnostic could be confused with accessor parent validation. Mitigation: both surfaces intentionally share `ValueError("client must be a Client")`, while this draft explicitly covers `PrivateMessageCollection.from_ids(...)` direct acquisition rather than accessor construction.

## Dependencies

- Existing `Client` remains the canonical parent type for direct private-message reads.
- Existing message-ID validators remain responsible for ID shape before client validation.
- Existing private-message retry, response, parser, and record validators remain responsible for authenticated detail acquisition after a valid client is provided.

## Open Questions

None for this local slice.

## Upstream-Safe Motivation

`PrivateMessageCollection.from_ids(...)` is the direct read entry point for private-message detail lookup. Validating the supplied client object before login and request work gives generated callers and tests deterministic errors for malformed inputs without changing live Wikidot behavior, request shape, retries, parsing, diagnostics, empty-batch behavior, or downstream accessor workflows.

## Local Evidence, Not For Upstream Paste

- The focused RED failures showed malformed direct `client` arguments crossing the public static read boundary and leaking `AttributeError` from `client.login_check()`.
- This slice only validates the `PrivateMessageCollection.from_ids(...)` caller-provided parent client for non-empty direct reads. It does not change private-message list acquisition, detail parser selectors, response-body diagnostics, message ID validation, retry controls, collection initialization, record field validation, send behavior, live site behavior, or authentication semantics for valid clients.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw private-message HTML, private message text, and private site data out of upstream discussion.
