# PR Draft: Validate Private Message Collection Retained ID State

## Summary

`PrivateMessageCollection.find(id)` validates malformed caller-provided search-key types before scanning stored messages, but the scan still compared each retained `message.id` directly against the search ID. After local fixtures, generated ledgers, serialized records, or rehydrated private-message collections have been mutated incorrectly, booleans and floats can satisfy Python equality against integer message IDs, while `None`, strings, lists, and negative IDs are treated as ordinary not-found misses instead of corrupted retained message-ID state.

This change validates each stored message's retained ID with the existing `_validate_private_message_id(...)` helper before comparing it to the caller search ID. Malformed retained message IDs now raise `ValueError("message_id must be an integer")`, negative retained message IDs now raise `ValueError("message_id must be non-negative")`, valid zero-ID lookup remains accepted, existing absent integer lookup behavior remains unchanged, and no direct private-message read, inbox/sent-box acquisition, parser, client accessor, retry, duplicate handling, or send behavior changes.

## Outcome

Loaded private-message collections can no longer return a message by Python's loose numeric equality or hide corrupted retained message IDs behind an ordinary not-found result.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who build browser-free private-message ledgers, moderation notifications, migration checks, inbox/sent-box audits, local fixtures, or serialized and rehydrated `PrivateMessageCollection` objects.

## Current Evidence

Local rollout-backed drafts already established private-message reads and message identity as practical workflow surfaces. [037-pr-retry-private-message-fetches.md](037-pr-retry-private-message-fetches.md), [054-pr-deduplicate-private-message-detail-fetches.md](054-pr-deduplicate-private-message-detail-fetches.md), [067-pr-deduplicate-direct-private-message-fetches.md](067-pr-deduplicate-direct-private-message-fetches.md), [073-pr-reuse-private-message-detail-parsing.md](073-pr-reuse-private-message-detail-parsing.md), [077-pr-skip-empty-private-message-fetch-batches.md](077-pr-skip-empty-private-message-fetch-batches.md), [089-pr-scope-private-message-detail-header.md](089-pr-scope-private-message-detail-header.md), [101-pr-ignore-private-message-row-pager-markup.md](101-pr-ignore-private-message-row-pager-markup.md), [102-pr-ignore-private-message-nested-row-markup.md](102-pr-ignore-private-message-nested-row-markup.md), [106-pr-preserve-private-message-body-spacing.md](106-pr-preserve-private-message-body-spacing.md), [119-pr-preserve-private-message-subject-spacing.md](119-pr-preserve-private-message-subject-spacing.md), [133-pr-reuse-private-message-list-first-page-body.md](133-pr-reuse-private-message-list-first-page-body.md), [163-pr-private-message-list-row-error-context.md](163-pr-private-message-list-row-error-context.md), [178-pr-private-message-list-fetch-failure-context.md](178-pr-private-message-list-fetch-failure-context.md), [184-pr-private-message-detail-fetch-context.md](184-pr-private-message-detail-fetch-context.md), [188-pr-private-message-detail-parse-context.md](188-pr-private-message-detail-parse-context.md), [206-pr-private-message-detail-response-body-context.md](206-pr-private-message-detail-response-body-context.md), [207-pr-private-message-list-response-body-context.md](207-pr-private-message-list-response-body-context.md), [272-pr-private-message-detail-timestamp-context.md](272-pr-private-message-detail-timestamp-context.md), [273-pr-private-message-detail-subject-body-context.md](273-pr-private-message-detail-subject-body-context.md), [287-pr-private-message-detail-timestamp-value-context.md](287-pr-private-message-detail-timestamp-value-context.md), [288-pr-private-message-detail-user-context.md](288-pr-private-message-detail-user-context.md), [321-pr-private-message-response-body-type-context.md](321-pr-private-message-response-body-type-context.md), [361-pr-validate-private-message-message-id-inputs.md](361-pr-validate-private-message-message-id-inputs.md), [381-pr-validate-private-message-find-id.md](381-pr-validate-private-message-find-id.md), [397-pr-validate-private-message-retry-controls.md](397-pr-validate-private-message-retry-controls.md), [425-pr-validate-private-message-collection-initialization.md](425-pr-validate-private-message-collection-initialization.md), [451-pr-validate-private-message-id-field.md](451-pr-validate-private-message-id-field.md), [546-pr-validate-private-message-read-client.md](546-pr-validate-private-message-read-client.md), [612-pr-validate-private-message-record-client.md](612-pr-validate-private-message-record-client.md), [613-pr-validate-private-message-participant-clients.md](613-pr-validate-private-message-participant-clients.md), [614-pr-validate-private-message-send-recipient-client.md](614-pr-validate-private-message-send-recipient-client.md), and [643-pr-validate-non-negative-private-message-ids.md](643-pr-validate-non-negative-private-message-ids.md) cover private-message acquisition, direct-detail lookup, retries, duplicate response reduction, parser diagnostics, response diagnostics, collection search-key type validation, collection shape, direct ID type/range, record/client coherence, participant-client coherence, direct read client validation, and send recipient-client validation.

This slice is not a duplicate of those drafts. Issue 381 validates caller-provided `PrivateMessageCollection.find(id=...)` search-key types before scanning stored messages, but it does not validate retained IDs already stored inside the collection. Issues 451 and 643 validate direct `PrivateMessage(id=...)` construction and direct lookup IDs, but they cannot cover a valid message whose ID is corrupted after construction and then reused in a collection. Issue 425 validates that collection entries are `PrivateMessage` objects, not that their retained IDs remain valid during later lookup. Issue 643 explicitly left collection `find(...)` lookup semantics unchanged.

## Related Issue / Non-Duplicate Analysis

Builds directly on [381-pr-validate-private-message-find-id.md](381-pr-validate-private-message-find-id.md), [425-pr-validate-private-message-collection-initialization.md](425-pr-validate-private-message-collection-initialization.md), [451-pr-validate-private-message-id-field.md](451-pr-validate-private-message-id-field.md), [612-pr-validate-private-message-record-client.md](612-pr-validate-private-message-record-client.md), [613-pr-validate-private-message-participant-clients.md](613-pr-validate-private-message-participant-clients.md), and [643-pr-validate-non-negative-private-message-ids.md](643-pr-validate-non-negative-private-message-ids.md).

No upstream issue was filed from this local workspace.

## Changes

- Validate each stored `PrivateMessage.id` before `PrivateMessageCollection.find(id)` compares it to the search key.
- Reject retained stored message IDs such as `None`, `True`, `False`, `"1"`, `1.0`, and `[]` with `ValueError("message_id must be an integer")`.
- Reject retained stored message IDs such as `-1` with `ValueError("message_id must be non-negative")`.
- Preserve valid zero-ID lookup, valid matching lookup, existing absent integer lookup behavior, malformed caller search-key type diagnostics, collection initialization, direct private-message reads, inbox/sent-box acquisition, parser diagnostics, duplicate handling, empty direct reads, client accessors, and private-message send behavior.
- Do not add caller search-key range validation in this slice.

## Type Of Change

- Input validation
- Retained private-message ID hardening
- Loaded collection lookup integrity
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `PrivateMessageCollection.find(id)` must reject retained stored `message.id` values such as `None`, `True`, `False`, `"1"`, `1.0`, and `[]` with `ValueError("message_id must be an integer")` before comparison. |
| R2 | `PrivateMessageCollection.find(id)` must reject retained stored `message.id=-1` with `ValueError("message_id must be non-negative")` before comparison. |
| R3 | Valid lookup where the stored message ID and search ID are both `0` must remain accepted. |
| R4 | Existing caller search-key type validation, valid matching lookup, existing absent integer lookup behavior, collection initialization, direct private-message reads, inbox/sent-box acquisition, parser diagnostics, duplicate handling, empty direct reads, client accessors, and private-message send behavior must remain green. |
| R5 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private message subjects, private message bodies, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R6 | Focused RED/GREEN, private-message module coverage, adjacent client coverage, full unit tests, lint, format, mypy, pyright, and whitespace gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Malformed retained stored message IDs fail before lookup comparison. | `test_find_rejects_message_with_malformed_retained_ids` failed RED for six malformed values: booleans and `1.0` could be accepted through Python equality, while `None`, `"1"`, and `[]` returned ordinary misses. The test passed GREEN after stored message ID validation. | Accepting booleans/floats, returning ordinary `None` misses for corrupted IDs, coercing values, or returning a message from corrupted retained ID state rejects this local completion claim. | Stored `PrivateMessage.id` during collection lookup | `src/wikidot/module/private_message.py`, `tests/unit/test_private_message.py` |
| R2 | Negative retained stored message IDs fail before lookup comparison. | `test_find_rejects_message_with_negative_retained_id` failed RED with an ordinary not-found result, then passed GREEN after stored message ID range validation. | Treating negative stored IDs as ordinary misses, accepting them, matching them, or coercing them rejects this local completion claim. | Stored `PrivateMessage.id` during collection lookup | `src/wikidot/module/private_message.py`, `tests/unit/test_private_message.py` |
| R3 | Zero remains a valid retained message ID for lookup. | `test_find_accepts_message_with_zero_retained_id` passed RED and GREEN. | Rejecting `0`, treating it as missing, coercing it to false, or changing returned message identity rejects this local completion claim. | Private-message collection lookup semantics | `tests/unit/test_private_message.py` |
| R4 | Existing compatible behavior remains compatible. | Focused GREEN coverage passed 8 tests, `tests/unit/test_private_message.py` passed 148 tests, adjacent private-message/client coverage passed 195 tests, and full unit passed 3213 tests. | Regressing caller search-key type validation, valid matching lookup, existing absent integer lookup behavior, collection initialization, direct detail reads, inbox acquisition, sent-box acquisition, duplicate direct lookup deduplication, response diagnostics, parser diagnostics, client accessors, private-message send behavior, or any unit test rejects this local completion claim. | Private-message collection and adjacent client workflows | `tests/unit/test_private_message.py`, `tests/unit/test_client.py`, `tests/unit` |
| R5 | No live site state or private material is needed to prove the behavior. | All regressions use synthetic private-message objects and local unit helpers only. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, raw response bodies, private message subjects, private message bodies, private site data, or raw private payloads rejects this local completion claim. | Test and draft privacy | this draft |
| R6 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN, targeted tests, full unit, ruff, format, mypy, temporary pyright, and whitespace checks passed. | Test, lint, format, type, pyright, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `782a5de fix(private_message): validate collection retained ids`.

- RED: `uv run pytest tests/unit/test_private_message.py::TestPrivateMessageCollection::test_find_accepts_message_with_zero_retained_id tests/unit/test_private_message.py::TestPrivateMessageCollection::test_find_rejects_message_with_malformed_retained_ids tests/unit/test_private_message.py::TestPrivateMessageCollection::test_find_rejects_message_with_negative_retained_id -q` collected 8 tests: 7 retained stored message-ID cases failed before the fix, and the zero-ID compatibility guard passed.
- GREEN: the same focused command passed 8 tests after stored message IDs were validated before collection lookup comparison.
- `uv run ruff format src/wikidot/module/private_message.py tests/unit/test_private_message.py` left both files unchanged.
- `uv run pytest tests/unit/test_private_message.py -q` passed 148 tests.
- `uv run pytest tests/unit/test_private_message.py tests/unit/test_client.py -q` passed 195 tests.
- `uv run pytest tests/unit -q` passed 3213 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run --with pyright pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `PrivateMessageCollection.find(1)` raises `ValueError("message_id must be an integer")` when a stored message's retained `message.id` is `None`, `"1"`, or `[]`.
- `PrivateMessageCollection.find(1)` for retained `True`, `find(0)` for retained `False`, and `find(1)` for retained `1.0` raise `ValueError("message_id must be an integer")` before Python equality can match those corrupted IDs.
- `PrivateMessageCollection.find(1)` raises `ValueError("message_id must be non-negative")` when a stored message's retained `message.id` is `-1`.
- `PrivateMessageCollection.find(0)` still returns a message whose retained ID is valid integer `0`.
- Existing malformed search-key type rejection, matching lookup, absent integer lookup behavior, collection initialization, direct private-message reads, inbox/sent-box acquisition, parser diagnostics, duplicate handling, empty direct reads, client accessors, and private-message send behavior remain green.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private message subjects, private message bodies, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

`PrivateMessageCollection.find(id)` is a local lookup over already loaded inbox/sent-box or direct private-message records. The caller search key already has type validation, and stored message rows should be held to the same retained-ID contract before comparison. Validating stored IDs prevents corrupted local state from matching through Python's bool/float equality rules or disappearing as an ordinary not-found result, while preserving valid zero IDs, existing absent integer behavior, and all parser/network behavior.

## Local Evidence

- Existing local drafts covered private-message fetch retry behavior, duplicate detail reduction, parse reuse, response diagnostics, parser field diagnostics, message ID input type validation, loaded collection search validation, collection constructor validation, direct message record ID type validation, retry controls, direct read client validation, record/client coherence, participant-client coherence, and direct message ID range validation.
- None of those drafts covered malformed retained stored `PrivateMessage.id` values inside `PrivateMessageCollection.find(...)` because the scan still compared `message.id == id` directly.
- The focused RED failure showed booleans and floats could be accepted as stored message IDs when they compared equal to lookup integers, while `None`, strings, lists, and negative IDs could be misreported as ordinary not-found results.
- This slice only validates retained stored message IDs at the loaded collection lookup comparison boundary. It does not change direct private-message acquisition, inbox/sent-box acquisition, parser field extraction, retry behavior, duplicate detail handling, client accessors, private-message send behavior, live site behavior, pushes, upstream Issues, or upstream PRs.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw login response bodies, private message subjects, private message bodies, private site data, and raw private payloads out of upstream discussion.

## Additional Notes

The change intentionally reuses `_validate_private_message_id(...)` only for stored collection rows. It does not add caller search-key range validation in `PrivateMessageCollection.find(...)`, preserving the prior lookup-surface scope from Issue 381 and the explicit Issue 643 note that direct private-message ID range validation did not change collection lookup semantics.
