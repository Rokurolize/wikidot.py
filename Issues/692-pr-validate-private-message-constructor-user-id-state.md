# PR Draft: Validate PrivateMessage Constructor Participant User ID State

## Summary

`PrivateMessage(...)` records already validate the parent client, message ID type and range, sender/recipient object type, sender/recipient client coherence, text fields, timestamps, send-recipient ID shape/range, and retained stored message IDs during collection lookup. One constructor retained-state gap remained: a valid same-client `User` could be mutated, fixture-loaded, or rehydrated with malformed retained `id` state and then stored as a new private-message `sender` or `recipient`.

This change validates retained constructor participant IDs after the existing `AbstractUser` type check and before participant/client coherence checks. Malformed retained `sender.id` or `recipient.id` values now raise `ValueError("<field>.id must be an integer or None")`, negative retained IDs now raise `ValueError("<field>.id must be non-negative or None")`, and valid optional `None` plus zero-ID compatibility remain accepted.

## Outcome

Direct `PrivateMessage(...)` rows cannot store malformed or negative retained sender/recipient IDs. Valid parser-created records, same-client direct rows, optional missing IDs, zero-ID compatibility, direct reads, inbox/sent-box acquisition, collection behavior, send behavior, client accessors, and adjacent user/client workflows remain unchanged.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who build browser-free private-message ledgers, moderation notifications, migration checks, inbox/sent-box audits, generated fixtures, or serialized and rehydrated `PrivateMessage` records.

## Current Evidence

Local rollout-backed drafts [037-pr-retry-private-message-fetches.md](037-pr-retry-private-message-fetches.md), [054-pr-deduplicate-private-message-detail-fetches.md](054-pr-deduplicate-private-message-detail-fetches.md), [067-pr-deduplicate-direct-private-message-fetches.md](067-pr-deduplicate-direct-private-message-fetches.md), [073-pr-reuse-private-message-detail-parsing.md](073-pr-reuse-private-message-detail-parsing.md), [077-pr-skip-empty-private-message-fetch-batches.md](077-pr-skip-empty-private-message-fetch-batches.md), [089-pr-scope-private-message-detail-header.md](089-pr-scope-private-message-detail-header.md), [106-pr-preserve-private-message-body-spacing.md](106-pr-preserve-private-message-body-spacing.md), [119-pr-preserve-private-message-subject-spacing.md](119-pr-preserve-private-message-subject-spacing.md), [133-pr-reuse-private-message-list-first-page-body.md](133-pr-reuse-private-message-list-first-page-body.md), [288-pr-private-message-detail-user-context.md](288-pr-private-message-detail-user-context.md), [360-pr-validate-private-message-send-recipients.md](360-pr-validate-private-message-send-recipients.md), [361-pr-validate-private-message-message-id-inputs.md](361-pr-validate-private-message-message-id-inputs.md), [425-pr-validate-private-message-collection-initialization.md](425-pr-validate-private-message-collection-initialization.md), [451-pr-validate-private-message-id-field.md](451-pr-validate-private-message-id-field.md), [498-pr-validate-private-message-record-fields.md](498-pr-validate-private-message-record-fields.md), [546-pr-validate-private-message-read-client.md](546-pr-validate-private-message-read-client.md), [612-pr-validate-private-message-record-client.md](612-pr-validate-private-message-record-client.md), [613-pr-validate-private-message-participant-clients.md](613-pr-validate-private-message-participant-clients.md), [614-pr-validate-private-message-send-recipient-client.md](614-pr-validate-private-message-send-recipient-client.md), [647-pr-validate-non-negative-user-ids.md](647-pr-validate-non-negative-user-ids.md), [674-pr-validate-private-message-collection-retained-id-state.md](674-pr-validate-private-message-collection-retained-id-state.md), and [685-pr-validate-private-message-send-recipient-id-range.md](685-pr-validate-private-message-send-recipient-id-range.md) establish private-message reads, sends, parser output, record construction, collection lookup, participant coherence, direct user-ID construction, and downstream mutable user-state validation as practical workflow surfaces.

This slice is not a duplicate of those drafts. Issue 498 validates that `sender` and `recipient` are `AbstractUser` objects; it does not validate retained participant ID state. Issue 613 validates participant/client coherence, not retained ID shape or range. Issue 674 validates retained `PrivateMessage.id` state during collection lookup, not retained participant user IDs. Issues 360 and 685 validate direct `PrivateMessage.send(...)` recipient IDs before mutation work; they do not validate stored message records. Issue 647 validates direct `User` and `DeletedUser` construction, but it cannot cover a valid user object whose public `id` is corrupted after construction and then stored in a private-message record.

## Related Issue / Non-Duplicate Analysis

Builds directly on [498-pr-validate-private-message-record-fields.md](498-pr-validate-private-message-record-fields.md), [613-pr-validate-private-message-participant-clients.md](613-pr-validate-private-message-participant-clients.md), [647-pr-validate-non-negative-user-ids.md](647-pr-validate-non-negative-user-ids.md), [674-pr-validate-private-message-collection-retained-id-state.md](674-pr-validate-private-message-collection-retained-id-state.md), and [685-pr-validate-private-message-send-recipient-id-range.md](685-pr-validate-private-message-send-recipient-id-range.md).

No upstream issue was filed from this local workspace.

## Changes

- Validate retained `sender.id` and `recipient.id` during `PrivateMessage.__post_init__`.
- Reject retained constructor participant IDs `True`, `False`, `"12345"`, `12345.0`, and `[]` with `ValueError("sender.id must be an integer or None")` or `ValueError("recipient.id must be an integer or None")`.
- Reject retained constructor participant ID `-1` with `ValueError("sender.id must be non-negative or None")` or `ValueError("recipient.id must be non-negative or None")`.
- Preserve retained constructor participant IDs `None` and `0`.
- Preserve existing message ID validation, parent client validation, participant object validation, participant/client coherence, subject/body validation, timestamp validation, direct private-message reads, inbox/sent-box acquisition, collection behavior, send behavior, client accessors, and adjacent user/client workflows.

## Type Of Change

- State validation
- Private-message constructor hardening
- Retained participant identity integrity
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `PrivateMessage(..., sender=user, ...)` and `PrivateMessage(..., recipient=user, ...)` must reject retained participant IDs `True`, `False`, `"12345"`, `12345.0`, and `[]` with `ValueError("<field>.id must be an integer or None")` before storing the message row. |
| R2 | `PrivateMessage(..., sender=user, ...)` and `PrivateMessage(..., recipient=user, ...)` must reject retained participant ID `-1` with `ValueError("<field>.id must be non-negative or None")` before storing the message row. |
| R3 | Valid retained participant IDs `None` and `0` must remain accepted in direct `PrivateMessage(...)` construction. |
| R4 | Existing malformed message ID validation, parent client validation, participant object validation, participant/client coherence, text field validation, timestamp validation, direct reads, inbox/sent-box acquisition, collection behavior, send behavior, client accessors, and adjacent user/client workflows must remain unchanged. |
| R5 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private message subjects, private message bodies, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R6 | Focused RED/GREEN, private-message tests, adjacent client/accessor/user tests, full unit tests, lint, format, type, pyright, and whitespace gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Malformed retained participant IDs fail at the direct constructor boundary. | `test_init_rejects_malformed_retained_user_ids` failed RED for ten malformed sender/recipient cases with `DID NOT RAISE`, then passed GREEN after `PrivateMessage.__post_init__` validated retained participant IDs. | Accepting booleans, numeric strings, floats, lists, coercing values, or deferring failure to later send or collection paths rejects this local completion claim. | `PrivateMessage` constructor | `src/wikidot/module/private_message.py`, `tests/unit/test_private_message.py` |
| R2 | Negative retained participant IDs fail at the direct constructor boundary. | `test_init_rejects_negative_retained_user_id` failed RED for sender and recipient with `DID NOT RAISE`, then passed GREEN after constructor retained-ID validation was added. | Accepting negative retained sender/recipient IDs, storing the row, or hiding the state behind later message handling rejects this local completion claim. | `PrivateMessage` constructor | `src/wikidot/module/private_message.py`, `tests/unit/test_private_message.py` |
| R3 | Optional missing and zero participant IDs remain compatible constructor state. | `test_init_accepts_optional_retained_user_ids` passed RED and GREEN for both sender and recipient with `None` and `0`, asserting the stored value is preserved. | Rejecting `None`, rejecting `0`, coercing either value, or requiring concrete regular-user IDs rejects this local completion claim. | `PrivateMessage` constructor | `tests/unit/test_private_message.py` |
| R4 | Existing private-message behavior and adjacent workflows remain green. | `tests/unit/test_private_message.py` passed 167 tests, adjacent private-message/client/accessor/user coverage passed 344 tests, and full unit coverage passed 3429 tests. | Regressing parser-created messages, constructor message/client/participant/text/time diagnostics, participant-client coherence, direct reads, inbox/sent-box acquisition, collection lookup, direct send validation, client accessors, user workflows, or any unit test rejects this local completion claim. | Private-message and adjacent workflows | `tests/unit` |
| R5 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level synthetic `Client`, `User`, and `PrivateMessage` objects only. | Using credentials, cookies, auth JSON, private message subjects, private message bodies, private recipient names from real messages, raw rollout paths, live Wikidot actions, pushes, upstream Issues, or upstream PRs rejects this local completion claim. | Test and draft privacy | this draft |
| R6 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN, private-message/adjacent/full-unit tests, ruff, format check, mypy, temporary pyright, and `git diff --check` passed. | Test, lint, format, type, pyright, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `bf48298 fix(private_message): validate constructor participant user ids`.

- RED: `uv run pytest tests/unit/test_private_message.py::TestPrivateMessage -k retained_user_id -q` selected 16 constructor retained-user-ID tests; 12 malformed or negative retained-ID cases failed before the fix with `DID NOT RAISE`, while the four `None` and zero-ID compatibility guards passed.
- GREEN: the same focused command passed 16 tests after constructor retained-ID validation was added.
- `uv run ruff format src/wikidot/module/private_message.py tests/unit/test_private_message.py` reformatted 1 file and left 1 file unchanged.
- `uv run pytest tests/unit/test_private_message.py -q` passed 167 tests.
- `uv run pytest tests/unit/test_private_message.py tests/unit/test_client.py tests/unit/test_client_accessors.py tests/unit/test_user.py -q` passed 344 tests.
- `uv run pytest tests/unit -q` passed 3429 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `git diff --check` passed.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run --with pyright pyright` passed with 0 errors, 0 warnings, and 0 informations.

## Acceptance Criteria

- `PrivateMessage(...)` raises `ValueError("sender.id must be an integer or None")` when the retained sender ID is `True`, `False`, `"12345"`, `12345.0`, or `[]`.
- `PrivateMessage(...)` raises `ValueError("recipient.id must be an integer or None")` when the retained recipient ID is `True`, `False`, `"12345"`, `12345.0`, or `[]`.
- `PrivateMessage(...)` raises `ValueError("sender.id must be non-negative or None")` when the retained sender ID is `-1`.
- `PrivateMessage(...)` raises `ValueError("recipient.id must be non-negative or None")` when the retained recipient ID is `-1`.
- Malformed or negative retained participant IDs fail before the message row is stored by direct construction.
- Valid retained participant IDs `None` and `0` remain accepted by direct construction.
- Existing malformed message ID validation, parent client validation, participant object validation, participant/client coherence validation, subject/body validation, timestamp validation, direct reads, inbox/sent-box acquisition, collection behavior, send behavior, client accessors, and adjacent user/client workflows remain green.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private message subjects, private message bodies, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.
- Private-data and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: Directly constructed private-message rows with corrupted retained participant IDs now fail during construction instead of later send or lookup paths. Mitigation: those values are impossible participant identity state; failing before storage is deterministic and field-specific.
- Risk: Optional participant IDs could be rejected accidentally. Mitigation: the focused compatibility guard asserts that `None` and `0` remain accepted and preserved for both sender and recipient.
- Risk: Validation precedence could regress earlier private-message diagnostics. Mitigation: the retained-ID check runs after participant type validation and before participant-client coherence; the full private-message and adjacent suites remain green.

## Dependencies

- Existing `User` constructor validation remains unchanged.
- Existing private-message ID validation, parent client validation, participant object validation, participant/client coherence, text validation, timestamp validation, direct read validation, collection behavior, and send behavior remain unchanged.

## Open Questions

None for this local slice. Remaining useful work should continue with fresh duplicate-checked public input boundaries, parser diagnostics, result ergonomics, action/read boundaries, retained cache/collection state, downstream mutable user-state preflights, or complexity candidates outside this now-covered `PrivateMessage` constructor retained participant user-ID boundary.

## Upstream-Safe Motivation

`PrivateMessage` is the durable row shape behind direct message reads, inbox/sent-box audits, private-message ledgers, migration checks, and local fixtures. Parser-created users may legitimately have optional IDs, while direct `User` construction already rejects impossible negative IDs. Constructor-side validation keeps corrupted fixture-loaded or rehydrated participant IDs out of stored private-message rows while preserving optional missing IDs, zero-ID compatibility, valid parser-created rows, client coherence, and send semantics.

## Local Evidence, Not For Upstream Paste

- Local rollout-backed work established private messages as a practical workflow through direct detail reads, mailbox acquisition, duplicate detail reuse, parser diagnostics, response diagnostics, text preservation, direct sends, collection lookup behavior, record validation, participant-client coherence, send recipient validation, and retained message-ID validation.
- Existing local drafts covered non-`AbstractUser` participants, participant-client mismatch, direct message IDs, collection message IDs, direct send recipient ID shape/range, and direct user constructor ID ranges; they did not validate corrupted retained `User.id` values at the direct `PrivateMessage(...)` constructor boundary.
- The focused RED failure showed malformed and negative retained sender/recipient IDs could be stored in direct message rows. The GREEN regressions cover constructor malformed/negative rejection, optional-ID and zero-ID constructor compatibility, private-message behavior, adjacent client/user workflows, and full unit compatibility.
- This slice only validates retained participant user IDs at the `PrivateMessage` constructor boundary. It does not change private-message detail parsing, inbox/sent-box acquisition, message list parsing, collection lookup behavior for valid rows, direct send payload construction, live site behavior, pushes, upstream Issues, or upstream PRs.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, private message subjects, private message bodies, raw action responses, source text from real sites, recipient names from real messages, and private site data out of upstream discussion.

## Additional Notes

The implementation intentionally accepts `None` for retained participant IDs instead of reusing the stricter send-recipient action preflight. Stored private-message participants may be parsed as deleted, guest, anonymous, system, or otherwise unresolved users, and this constructor slice only rejects malformed or negative retained identity state.
