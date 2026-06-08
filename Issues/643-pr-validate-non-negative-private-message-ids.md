# PR Draft: Validate Non-Negative PrivateMessage IDs

## Summary

`PrivateMessage.id`, `PrivateMessage.from_id(...)`, `PrivateMessageCollection.from_ids(...)`, and `client.private_message.get_message(...)` / `get_messages(...)` identify concrete dashboard private messages used by browser-free inbox/sent-box reads, direct private-message detail reads, duplicate direct-message reuse, generated PM audit ledgers, moderation or migration tooling, local fixtures, and rehydrated records. Existing local drafts validate message IDs as non-boolean integers, but direct constructors and direct lookup helpers still accepted negative integers such as `-1`. Negative lookup IDs could advance into login, retry configuration, or response mapping before failing with unrelated low-level errors.

This change validates direct `PrivateMessage.id`, single-message lookup IDs, and batch message lookup IDs as non-negative integers at the shared validation boundary. It deliberately preserves `id=0` and lookup `message_id=0` because prior identity-field drafts avoid stronger positive-ID requirements unless parser or live evidence proves one.

## Outcome

Directly constructed private-message records and direct private-message lookup calls can no longer store or submit negative message IDs, while zero-ID compatibility, malformed direct type diagnostics, direct PM reads, inbox/sent-box acquisition, duplicate lookup deduplication, parser diagnostics, collection lookup, client accessors, and send behavior remain unchanged.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use browser-free private-message detail reads, inbox/sent-box acquisition, generated PM audit ledgers, moderation notifications, migration checks, `Client.private_message.get_message(...)`, `Client.private_message.get_messages(...)`, local fixtures, or serialized/rehydrated private-message records.

## Current Evidence

Local rollout-backed drafts repeatedly identify private-message reads and stored message records as practical workflow surfaces. [037-pr-retry-private-message-fetches.md](037-pr-retry-private-message-fetches.md), [054-pr-deduplicate-private-message-detail-fetches.md](054-pr-deduplicate-private-message-detail-fetches.md), [067-pr-deduplicate-direct-private-message-fetches.md](067-pr-deduplicate-direct-private-message-fetches.md), [073-pr-reuse-private-message-detail-parsing.md](073-pr-reuse-private-message-detail-parsing.md), [077-pr-skip-empty-private-message-fetch-batches.md](077-pr-skip-empty-private-message-fetch-batches.md), [321-pr-private-message-response-body-type-context.md](321-pr-private-message-response-body-type-context.md), and [546-pr-validate-private-message-read-client.md](546-pr-validate-private-message-read-client.md) establish private-message direct reads, list reads, retry behavior, response diagnostics, duplicate handling, and direct read client validation as practical surfaces. [361-pr-validate-private-message-message-id-inputs.md](361-pr-validate-private-message-message-id-inputs.md) validates direct lookup input types. [381-pr-validate-private-message-find-id.md](381-pr-validate-private-message-find-id.md) validates loaded-collection lookup ID types. [451-pr-validate-private-message-id-field.md](451-pr-validate-private-message-id-field.md) validates direct `PrivateMessage.id` type.

This slice is not a duplicate of Issues 361, 381, 397, 451, or 546. Issue 361 rejects non-lists, booleans, strings, floats, and other malformed direct lookup IDs, but still accepts negative integer IDs. Issue 381 validates already-loaded collection search-key shape, and this slice intentionally does not alter `find(...)` semantics. Issue 397 validates retry-control ranges, not message identity ranges. Issue 451 rejects malformed direct constructor ID types, but still accepts negative integers. Issue 546 validates the caller-provided client object after valid non-empty ID preflight.

## Related Issue / Non-Duplicate Analysis

Builds directly on [361-pr-validate-private-message-message-id-inputs.md](361-pr-validate-private-message-message-id-inputs.md), [381-pr-validate-private-message-find-id.md](381-pr-validate-private-message-find-id.md), [451-pr-validate-private-message-id-field.md](451-pr-validate-private-message-id-field.md), and [546-pr-validate-private-message-read-client.md](546-pr-validate-private-message-read-client.md).

No upstream issue was filed from this local workspace.

## Changes

- Reject direct `PrivateMessage(id=-1)` with `ValueError("message_id must be non-negative")`.
- Reject direct `PrivateMessage.from_id(client, -1)` and `client.private_message.get_message(-1)` with `ValueError("message_id must be non-negative")` before login, retry config, or AMC request work.
- Reject direct `PrivateMessageCollection.from_ids(client, [-1])` and `client.private_message.get_messages([-1])` with `ValueError("message_ids list entries must be non-negative")` before login, retry config, or AMC request work.
- Preserve direct `PrivateMessage(id=0)` and direct lookup `message_id=0` as non-negative identity values.
- Preserve existing malformed-ID diagnostics for non-integers and booleans.
- Leave inbox/sent-box parsing, direct detail parsing, duplicate direct lookup deduplication, collection `find(...)` lookup semantics, client accessor delegation, and private-message send behavior unchanged.

## Type Of Change

- Input validation
- Public dataclass constructor behavior hardening
- Public direct-read input-boundary hardening
- Private-message identity state integrity
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | Direct `PrivateMessage(id=-1)` must raise `ValueError("message_id must be non-negative")` when every other message field is valid. |
| R2 | Direct `PrivateMessage.from_id(client, -1)` and `client.private_message.get_message(-1)` must raise `ValueError("message_id must be non-negative")` before login, retry config, or AMC work. |
| R3 | Direct `PrivateMessageCollection.from_ids(client, [-1])` and `client.private_message.get_messages([-1])` must raise `ValueError("message_ids list entries must be non-negative")` before login, retry config, or AMC work. |
| R4 | Direct `PrivateMessage(id=0)` and direct lookup `message_id=0` must remain valid and store/request `0`. |
| R5 | Existing malformed direct ID and lookup diagnostics must remain stable. |
| R6 | Direct private-message reads, inbox/sent-box acquisition, duplicate direct lookup deduplication, parser diagnostics, collection lookup, client accessors, and send behavior must remain unchanged. |
| R7 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private message bodies, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R8 | Focused RED/GREEN, private-message/client tests, full unit tests, lint, format, mypy, pyright, and whitespace gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Direct private-message records cannot store negative message IDs. | `TestPrivateMessage.test_init_rejects_negative_message_id` failed RED with `DID NOT RAISE`, then passed GREEN after `_validate_private_message_id(...)` rejected values below zero. | Accepting negative message IDs, coercing them to zero, or deferring failure to parser or lookup code rejects this local completion claim. | PrivateMessage constructor | `src/wikidot/module/private_message.py`, `tests/unit/test_private_message.py` |
| R2 | Single direct message lookup rejects negative IDs before login, retry config, or request work. | `TestPrivateMessage.test_from_id_rejects_negative_message_id_before_login` failed RED because `-1` reached response mapping and leaked `KeyError: -1`; `TestClientPrivateMessageAccessor.test_get_message_rejects_negative_message_id` failed RED by reaching retry config and surfacing an unrelated batch-size error. Both passed GREEN after single-ID range validation. | Calling `client.login_check()`, reading retry config, calling `client.amc_client.request(...)`, submitting negative `item` payloads, or surfacing response-mapping/retry-control errors rejects this local completion claim. | Direct single message lookup | `src/wikidot/module/private_message.py`, `src/wikidot/module/client.py`, `tests/unit/test_private_message.py`, `tests/unit/test_client.py` |
| R3 | Batch direct message lookup rejects negative IDs before login, retry config, or request work. | `TestPrivateMessageCollection.test_from_ids_rejects_negative_message_id_entries_before_login` failed RED by reaching the retry-aware detail path and leaking `KeyError: -1`; `TestClientPrivateMessageAccessor.test_get_messages_rejects_negative_message_id` failed RED by reaching retry config and surfacing an unrelated batch-size error. Both passed GREEN after batch-ID range validation. | Submitting negative `item` payloads, deduplicating invalid negative IDs, or surfacing low-level mapping/retry-control failures rejects this local completion claim. | Direct batch message lookup | `src/wikidot/module/private_message.py`, `src/wikidot/module/client.py`, `tests/unit/test_private_message.py`, `tests/unit/test_client.py` |
| R4 | Zero remains valid for direct message IDs. | `TestPrivateMessage.test_init_accepts_zero_message_id` and `TestPrivateMessageCollection.test_from_ids_accepts_zero_message_id` passed in RED and GREEN runs. | Requiring positive-only message IDs without separate evidence rejects this local completion claim. | Constructor and direct lookup compatibility | `tests/unit/test_private_message.py` |
| R5 | Existing malformed direct type diagnostics remain stable. | Existing malformed constructor, batch lookup, and single lookup ID tests passed in the same focused RED and GREEN commands. | Changing `ValueError("message_id must be an integer")`, `ValueError("message_ids list entries must be integers")`, or `ValueError("message_ids must be a list")`, accepting booleans, or coercing strings/floats rejects this local completion claim. | PrivateMessage ID type validation | `tests/unit/test_private_message.py` |
| R6 | Existing private-message and client workflows remain green. | `tests/unit/test_private_message.py tests/unit/test_client.py` passed 187 tests, and the full unit suite passed 2913 tests. | Regressing direct detail reads, inbox/sent-box acquisition, duplicate direct lookup deduplication, response diagnostics, parser diagnostics, client accessors, collection lookup, private-message send behavior, or adjacent client workflows rejects this local completion claim. | Private-message and client workflows | `tests/unit/test_private_message.py`, `tests/unit/test_client.py`, `tests/unit` |
| R7 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level tests only. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, raw response bodies, private message subjects, private message bodies, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R8 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN, private-message/client tests, full unit, ruff, format, mypy, pyright, and whitespace checks passed. | Test, lint, format, type, pyright, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `9ea0eb8 fix(private_message): validate non-negative message ids`.

- RED: `uv run pytest tests/unit/test_private_message.py::TestPrivateMessageCollection::test_from_ids_rejects_non_integer_message_id_entries_before_login tests/unit/test_private_message.py::TestPrivateMessageCollection::test_from_ids_rejects_negative_message_id_entries_before_login tests/unit/test_private_message.py::TestPrivateMessageCollection::test_from_ids_accepts_zero_message_id tests/unit/test_private_message.py::TestPrivateMessage::test_init_rejects_non_integer_message_id tests/unit/test_private_message.py::TestPrivateMessage::test_init_rejects_negative_message_id tests/unit/test_private_message.py::TestPrivateMessage::test_init_accepts_zero_message_id tests/unit/test_private_message.py::TestPrivateMessage::test_from_id_rejects_non_integer_message_id_before_login tests/unit/test_private_message.py::TestPrivateMessage::test_from_id_rejects_negative_message_id_before_login tests/unit/test_client.py::TestClientPrivateMessageAccessor::test_get_messages_rejects_negative_message_id tests/unit/test_client.py::TestClientPrivateMessageAccessor::test_get_message_rejects_negative_message_id -q` failed 5 negative constructor, direct lookup, batch lookup, and client-accessor ID cases before the fix; 13 malformed-input and zero-compatibility guards stayed green.
- GREEN: the same focused command passed 18 tests after direct message-ID and message-ID list range validation was added.
- `uv run ruff format src/wikidot/module/private_message.py tests/unit/test_private_message.py tests/unit/test_client.py` left all 3 files unchanged.
- Re-running the same focused command after formatting passed 18 tests.
- `uv run pytest tests/unit/test_private_message.py tests/unit/test_client.py -q` passed 187 tests.
- `uv run pytest tests/unit -q` passed 2913 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `PrivateMessage(id=-1)` raises `ValueError("message_id must be non-negative")`.
- `PrivateMessage.from_id(client, -1)` and `client.private_message.get_message(-1)` raise `ValueError("message_id must be non-negative")` before login, retry config, or AMC work.
- `PrivateMessageCollection.from_ids(client, [-1])` and `client.private_message.get_messages([-1])` raise `ValueError("message_ids list entries must be non-negative")` before login, retry config, or AMC work.
- `PrivateMessage(id=0)` remains accepted and stores `0`.
- `PrivateMessageCollection.from_ids(client, [0])` remains accepted and submits a `{"item": 0, "moduleName": "dashboard/messages/DMViewMessageModule"}` request when the caller deliberately asks for message ID zero.
- `PrivateMessage(id=None)`, `True`, `"1"`, and `1.25` continue to raise `ValueError("message_id must be an integer")`.
- `PrivateMessageCollection.from_ids(client, [None])`, `[True]`, `["1"]`, and `[1.25]` continue to raise `ValueError("message_ids list entries must be integers")`.
- Direct PM reads, inbox/sent-box acquisition, duplicate direct lookup deduplication, parser diagnostics, response diagnostics, collection lookup, client accessors, and private-message send behavior remain green.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private message bodies, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

Private-message IDs are identity metadata for browser-free inbox/sent-box reads, direct detail lookups, duplicate direct-message reuse, generated PM audit ledgers, moderation summaries, local fixtures, and rehydrated records. Negative IDs can look like valid integer state in direct fixtures or generated lookup queues but are not useful message identifiers in the current public API surface. Non-negative validation catches that impossible state early while avoiding a stronger positive-only rule.

## Local Evidence

- Local rollout evidence used private-message direct reads, inbox/sent-box acquisition, duplicate direct-message reuse, generated private-message ledgers, client accessors, and records that construct or consume `PrivateMessage` objects directly.
- Existing local drafts covered private-message fetch retry behavior, duplicate detail reduction, parse reuse, response diagnostics, parser field diagnostics, message ID input type validation, loaded collection search validation, collection constructor validation, direct message record ID type validation, retry controls, and direct read client validation, but did not cover negative direct message IDs or lookup IDs.
- The focused RED failures showed negative direct constructor IDs were accepted and negative direct lookup IDs advanced into login/retry/request mapping. The GREEN regressions cover invalid values, zero compatibility, and existing malformed type validation.
- This slice only validates non-negative direct message-ID semantics. It does not change generated list/detail parsing, collection `find(...)` lookup semantics, direct-detail selectors, inbox/sent-box selectors, sender/recipient parsing, subject/body parsing, timestamp parsing, send behavior, live site behavior, or upstream actions.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw login response bodies, raw private-message subjects, raw private-message bodies, and private site data out of upstream discussion.

## Additional Notes

This change intentionally validates non-negative direct private-message IDs only. It does not require positive IDs, coerce numeric strings, or change `PrivateMessageCollection.find(...)` lookup semantics because prior local search-key drafts preserved absent integer lookup behavior while generated parser IDs already have their own diagnostics.
