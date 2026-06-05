# PR Draft: Validate Private Message ID Inputs

## Summary

`PrivateMessageCollection.from_ids(client, message_ids)`, `PrivateMessageInbox.from_ids(...)`, `PrivateMessageSentBox.from_ids(...)`, `PrivateMessage.from_id(client, message_id)`, and `client.private_message.get_messages/get_message(...)` document message IDs as integers, but malformed caller-provided ID inputs were not rejected at the public API boundary. A string such as `"12"` could be treated as an iterable batch of `"1"` and `"2"`, while entries such as `None`, `True`, `"1"`, or `1.25` could pass the login check and reach AMC request construction or detail response mapping before leaking unstable low-level failures such as `KeyError`.

This change validates private-message direct lookup IDs before login checks, empty/non-empty request handling, duplicate-ID deduplication, AMC request construction, retry handling, or detail parsing. Invalid batch values now raise `ValueError("message_ids must be a list")` or `ValueError("message_ids list entries must be integers")`; invalid single-message values now raise `ValueError("message_id must be an integer")`. Empty valid batches remain a no-login no-op, and valid non-empty reads keep the existing login, retry, deduplication, forbidden-message mapping, parser diagnostics, inbox/sentbox wrappers, and client accessor behavior.

## Outcome

Private-message read callers now get deterministic Python-side preflight validation for malformed message ID inputs instead of accidental login work, malformed AMC payloads, string-character ID requests, bool-as-int IDs, or low-level detail lookup failures.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators using browser-free private-message reads for moderation inbox checks, private audit ledgers, notification verification, migration tooling, or local scripts that pass message IDs from generated records, CLI flags, JSON, spreadsheets, or previous crawl output.

## Current Evidence

Local rollout evidence repeatedly treats private-message retrieval as a practical read surface. Existing drafts [037-pr-retry-private-message-fetches.md](037-pr-retry-private-message-fetches.md), [054-pr-deduplicate-private-message-detail-fetches.md](054-pr-deduplicate-private-message-detail-fetches.md), [067-pr-deduplicate-direct-private-message-fetches.md](067-pr-deduplicate-direct-private-message-fetches.md), [073-pr-reuse-private-message-detail-parsing.md](073-pr-reuse-private-message-detail-parsing.md), [077-pr-skip-empty-private-message-fetch-batches.md](077-pr-skip-empty-private-message-fetch-batches.md), [184-pr-private-message-detail-fetch-context.md](184-pr-private-message-detail-fetch-context.md), [188-pr-private-message-detail-parse-context.md](188-pr-private-message-detail-parse-context.md), and [321-pr-private-message-response-body-type-context.md](321-pr-private-message-response-body-type-context.md) establish direct private-message detail reads and client accessors as active practical workflows.

Those prior slices are not duplicates. They covered retry behavior, direct/list deduplication, duplicate response reuse, empty valid batch no-op behavior, fetch context, parser context, malformed response bodies, and private-message send validation. They did not validate caller-provided `message_ids` or `message_id` inputs before login checks, direct detail request construction, retry batches, or detail response remapping. This slice follows the recent input-boundary pattern from [355-pr-validate-private-message-send-text-inputs.md](355-pr-validate-private-message-send-text-inputs.md) and [360-pr-validate-private-message-send-recipients.md](360-pr-validate-private-message-send-recipients.md), but applies it to private-message read IDs.

## Related Issue

Builds directly on [067-pr-deduplicate-direct-private-message-fetches.md](067-pr-deduplicate-direct-private-message-fetches.md), [073-pr-reuse-private-message-detail-parsing.md](073-pr-reuse-private-message-detail-parsing.md), and [077-pr-skip-empty-private-message-fetch-batches.md](077-pr-skip-empty-private-message-fetch-batches.md).

No upstream issue was filed from this local workspace.

## Changes

- Validate `message_ids` is a `list` before checking its length or logging in.
- Validate every `message_ids` entry is a non-boolean integer before duplicate-ID deduplication or AMC request construction.
- Validate `PrivateMessage.from_id(..., message_id=...)` receives a non-boolean integer before delegating to the batch path.
- Preserve `PrivateMessageInbox.from_ids(...)`, `PrivateMessageSentBox.from_ids(...)`, and `client.private_message.get_messages/get_message(...)` through the same public validation path.
- Preserve valid empty batch behavior, valid non-empty login behavior, first-seen duplicate-ID request deduplication, duplicate output ordering, retry handling, `no_message` forbidden mapping, parser diagnostics, and successful direct reads.

## Type Of Change

- Input validation
- Public API behavior hardening
- Private-message read preflight safety
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `PrivateMessageCollection.from_ids(..., message_ids=...)` must reject non-list batch inputs with `ValueError("message_ids must be a list")` before login checks or AMC requests. |
| R2 | `PrivateMessageCollection.from_ids(..., message_ids=[...])` must reject non-integer and boolean entries with `ValueError("message_ids list entries must be integers")` before login checks or AMC requests. |
| R3 | `PrivateMessage.from_id(..., message_id=...)` must reject non-integer and boolean single IDs with `ValueError("message_id must be an integer")` before login checks or AMC requests. |
| R4 | `client.private_message.get_messages(...)` and `client.private_message.get_message(...)` must reach the same validation path for malformed inputs. |
| R5 | Valid empty batches, valid non-empty direct reads, duplicate-ID deduplication, duplicate output ordering, inbox/sentbox wrappers, retry behavior, forbidden-message mapping, and parser diagnostics must remain unchanged. |
| R6 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private message bodies/subjects, private recipient data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R7 | Focused RED/GREEN, adjacent private-message/client tests, full unit tests, lint, format, type, and whitespace gates must pass before claiming this local implementation complete; unavailable tools must be reported instead of hidden. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Non-list batch ID inputs fail before login or AMC request work. | `TestPrivateMessageCollection.test_from_ids_rejects_non_list_message_ids_before_login` failed RED before the fix by treating `"12"` as iterable IDs and leaking `KeyError: '1'`, then passed GREEN after validation was added. | Calling `client.login_check()`, calling `client.amc_client.request(...)`, accepting strings as ID batches, or splitting a string into per-character message IDs rejects this local completion claim. | Direct private-message batch read preflight | `src/wikidot/module/private_message.py`, `tests/unit/test_private_message.py` |
| R2 | Batch entries without real integer IDs fail before login or AMC request work. | `TestPrivateMessageCollection.test_from_ids_rejects_non_integer_message_id_entries_before_login` failed RED for `None`, `True`, `"1"`, and `1.25` by reaching the detail path and leaking `KeyError`, then passed GREEN after entry validation was added. | Treating `bool` as an integer ID, submitting non-integer `item` values, deduplicating invalid entries, or surfacing `KeyError` rejects this local completion claim. | Direct private-message batch entry preflight | `src/wikidot/module/private_message.py`, `tests/unit/test_private_message.py` |
| R3 | Single-message lookup inputs without real integer IDs fail before login or AMC request work. | `TestPrivateMessage.test_from_id_rejects_non_integer_message_id_before_login` failed RED by delegating malformed IDs into the batch detail path and leaking `KeyError`, then passed GREEN after single-ID validation was added. | Returning the batch error wording for a single-ID API, calling login, calling AMC, or accepting `True` as message ID `1` rejects this local completion claim. | Direct private-message single read preflight | `src/wikidot/module/private_message.py`, `tests/unit/test_private_message.py` |
| R4 | Client private-message accessors expose the same validation behavior. | `TestClientPrivateMessageAccessor.test_get_messages_rejects_non_list_message_ids` and `test_get_message_rejects_non_integer_message_id` pass through the real accessor path and assert login/AMC are not called. | Mock-only accessor coverage, bypassing `PrivateMessageCollection.from_ids(...)` or `PrivateMessage.from_id(...)`, or letting malformed accessor inputs reach login rejects this local completion claim. | Client private-message accessor | `src/wikidot/module/client.py`, `tests/unit/test_client.py` |
| R5 | Valid private-message reads and existing diagnostics remain unchanged. | Adjacent private-message/client tests passed 67 tests; the full unit suite passed 988 tests. | Regressing empty valid batch no-op behavior, valid non-empty login behavior, request deduplication, duplicate output ordering, retry behavior, `no_message` mapping, parser context, inbox/sentbox wrappers, send behavior, or client accessor delegation rejects this local completion claim. | Private-message workflow | `tests/unit/test_private_message.py`, `tests/unit/test_client.py` |
| R6 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level tests only with synthetic IDs and no real private-message content. | Using credentials, cookies, auth JSON, live Wikidot actions, raw rollout paths, sandbox details, upstream Issues, upstream PRs, private message bodies, private message subjects, real recipient names, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R7 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, adjacent tests passed, full unit passed, ruff, format, mypy, and whitespace checks passed; pyright was unavailable. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `f522f8f fix(private_message): validate message id inputs`.

- RED: `.venv/bin/python -m pytest -q tests/unit/test_private_message.py::TestPrivateMessageCollection::test_from_ids_rejects_non_list_message_ids_before_login tests/unit/test_private_message.py::TestPrivateMessageCollection::test_from_ids_rejects_non_integer_message_id_entries_before_login tests/unit/test_private_message.py::TestPrivateMessage::test_from_id_rejects_non_integer_message_id_before_login` failed before the fix with 8 failures; the batch and single-ID paths leaked `KeyError` after reaching the detail lookup path.
- GREEN: `.venv/bin/python -m pytest -q tests/unit/test_private_message.py::TestPrivateMessageCollection::test_from_ids_rejects_non_list_message_ids_before_login tests/unit/test_private_message.py::TestPrivateMessageCollection::test_from_ids_rejects_non_integer_message_id_entries_before_login tests/unit/test_private_message.py::TestPrivateMessage::test_from_id_rejects_non_integer_message_id_before_login tests/unit/test_client.py::TestClientPrivateMessageAccessor::test_get_messages_rejects_non_list_message_ids tests/unit/test_client.py::TestClientPrivateMessageAccessor::test_get_message_rejects_non_integer_message_id` passed 10 tests.
- `.venv/bin/python -m pytest -q tests/unit/test_private_message.py tests/unit/test_client.py::TestClientPrivateMessageAccessor` passed 67 tests.
- `.venv/bin/python -m pytest -q tests/unit` passed 988 tests.
- `ruff check .` passed.
- `ruff format --check .` passed with 81 files already formatted.
- `.venv/bin/mypy src tests` passed with no issues in 81 source files.
- `git diff --check` passed.

Not run successfully: `pyright src tests` was unavailable because neither `.venv/bin/pyright` nor a PATH `pyright` executable existed in this environment.

## Acceptance Criteria

- `PrivateMessageCollection.from_ids(client, "12")` raises `ValueError("message_ids must be a list")` before `client.login_check()` or `client.amc_client.request(...)`.
- `PrivateMessageCollection.from_ids(client, [None])`, `[True]`, `["1"]`, and `[1.25]` raise `ValueError("message_ids list entries must be integers")` before login or AMC work.
- `PrivateMessage.from_id(client, None)`, `True`, or `"1"` raises `ValueError("message_id must be an integer")` before login or AMC work.
- `client.private_message.get_messages(...)` and `client.private_message.get_message(...)` reach the same validation path for malformed inputs.
- `PrivateMessageCollection.from_ids(client, [])` still returns an empty collection without login or AMC work.
- Valid non-empty direct reads still call `client.login_check()` and submit `dashboard/messages/DMViewMessageModule` request bodies with integer `item` values.
- Existing duplicate-ID request deduplication, duplicate output ordering, retry behavior, `no_message` forbidden mapping, message detail parser diagnostics, inbox/sentbox acquisition, client accessor delegation, and private-message send behavior remain unchanged.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private message bodies/subjects, private recipient data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

Direct private-message lookup IDs often come from previous crawler output, CLI input, JSON, or generated ledgers. These inputs should fail deterministically at the public API boundary when malformed, especially because the direct lookup path performs authenticated dashboard reads and builds one AMC request per unique message ID. The change is narrow: it rejects malformed values instead of coercing them and leaves valid read behavior unchanged.

## Local Evidence, Not For Upstream Paste

- Local rollout evidence established private-message retrieval and direct message accessors as practical workflows.
- The focused RED failures showed malformed direct ID inputs crossing into login/detail lookup flow and leaking unstable `KeyError` failures instead of failing at the public call boundary.
- Existing private-message read drafts covered retry behavior, empty valid batches, duplicate ID deduplication, response reuse, and parser diagnostics, but not malformed public ID input preflight.
- This slice only validates private-message direct lookup ID inputs. It does not change private-message detail parsing, inbox/sentbox acquisition, empty valid lookup behavior, retry semantics, returned action-status validation, client authentication, live Wikidot behavior, or message dataclass fields.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, cookies, auth JSON, raw action responses, private message bodies, private message subjects, recipient names from real messages, page source text from real sites, and private site data out of upstream discussion.

## Additional Notes

The change intentionally rejects malformed values instead of coercing strings, floats, or booleans into IDs. Callers that receive private-message IDs from text sources should parse and validate them as integers before calling wikidot.py direct private-message lookup helpers.
