# PR Draft: Validate PrivateMessage.send Recipient ID Range

## Summary

`PrivateMessage.send(client, recipient, subject, body)` already validates send text inputs, the recipient object type, recipient ID type, recipient name type, recipient client ownership, action status, direct user record IDs at construction, and direct private-message IDs. The send path still accepted a retained `recipient.id` that was an integer below zero after a valid `User` was mutated, fixture-loaded, or rehydrated. That invalid retained ID could reach login, `DashboardMessageAction` request construction, mocked AMC handling, or returned action-status diagnostics instead of producing deterministic local recipient-ID validation.

This change validates the retained private-message send recipient ID range before login or AMC request work. Negative retained recipient IDs now raise `ValueError("recipient.id must be non-negative")`, valid zero recipient IDs remain accepted, and successful sends still use the existing `DashboardMessageAction` payload, recipient client validation, text validation, returned action-status validation, and no-return successful behavior.

## Outcome

Private-message sends no longer authenticate, build `to_user_id` payloads, or diagnose send action-status failures through impossible negative retained user IDs. Valid sends, zero-ID compatibility, malformed recipient type validation, recipient client validation, subject/body validation, action-status diagnostics, client private-message accessor behavior, and adjacent private-message/user workflows remain unchanged.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use browser-free private messages, generated notification workflows, moderation tooling, local fixtures, serialized user records, or rehydrated `User` objects before calling `PrivateMessage.send(...)` or `client.private_message.send(...)`.

## Current Evidence

Private-message send drafts [254-pr-private-message-send-action-status-context.md](254-pr-private-message-send-action-status-context.md), [355-pr-validate-private-message-send-text-inputs.md](355-pr-validate-private-message-send-text-inputs.md), [360-pr-validate-private-message-send-recipients.md](360-pr-validate-private-message-send-recipients.md), and [614-pr-validate-private-message-send-recipient-client.md](614-pr-validate-private-message-send-recipient-client.md) establish `PrivateMessage.send(...)`, send payloads, recipient validation, text input validation, recipient client coherence, and returned action-status diagnostics as practical mutation-boundary surfaces.

Related user and private-message ID drafts [647-pr-validate-non-negative-user-ids.md](647-pr-validate-non-negative-user-ids.md), [646-pr-validate-non-negative-quickmodule-user-ids.md](646-pr-validate-non-negative-quickmodule-user-ids.md), [579-pr-validate-private-message-collection-retained-ids.md](579-pr-validate-private-message-collection-retained-ids.md), and [674-pr-validate-private-message-collection-retained-id-state.md](674-pr-validate-private-message-collection-retained-id-state.md) establish direct user-ID range validation, QuickModule user-ID range validation, and private-message record retained message-ID validation as active operational boundaries.

This slice is not a duplicate of those drafts. Issue 360 validates the recipient is a `User`, that `recipient.id` is an integer and not a boolean, and that `recipient.name` is a string, but it still accepts negative integer recipient IDs. Issue 614 validates that the recipient belongs to the sending client, not the retained ID range. Issue 647 validates direct `User` and `DeletedUser` construction, but explicitly leaves downstream mutable user-state action preflights for separate duplicate-checked slices. Issues 579 and 674 validate private message record IDs, not user IDs used as send recipients.

## Related Issue / Non-Duplicate Analysis

Builds directly on [254-pr-private-message-send-action-status-context.md](254-pr-private-message-send-action-status-context.md), [355-pr-validate-private-message-send-text-inputs.md](355-pr-validate-private-message-send-text-inputs.md), [360-pr-validate-private-message-send-recipients.md](360-pr-validate-private-message-send-recipients.md), [614-pr-validate-private-message-send-recipient-client.md](614-pr-validate-private-message-send-recipient-client.md), and [647-pr-validate-non-negative-user-ids.md](647-pr-validate-non-negative-user-ids.md).

No upstream issue was filed from this local workspace.

## Changes

- Validate `recipient.id` is non-negative inside the existing private-message send recipient preflight.
- Reject retained send recipient IDs `-1` and `-100` with `ValueError("recipient.id must be non-negative")` before login or AMC request work.
- Preserve valid retained recipient ID `0` and submit it as `to_user_id: 0`.
- Preserve existing recipient object validation, recipient ID type validation, recipient name validation, recipient client validation, subject/body validation, action-status diagnostics, client accessor behavior, and successful send behavior.

## Type Of Change

- State validation
- Private-message send mutation-boundary hardening
- Retained user identity integrity
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `PrivateMessage.send(...)` must reject retained `recipient.id=-1` and `recipient.id=-100` with `ValueError("recipient.id must be non-negative")` before login, AMC request construction, action-status parsing, or send diagnostics use the value. |
| R2 | Valid retained recipient ID `0` must remain accepted and must produce a request payload with `to_user_id: 0`. |
| R3 | Existing non-`User` recipient validation, malformed recipient ID type validation, malformed recipient name validation, recipient client validation, subject/body validation, action-status diagnostics, client accessor behavior, and adjacent private-message/user workflows must remain unchanged. |
| R4 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private recipient data, private message bodies/subjects, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R5 | Focused RED/GREEN, private-message tests, adjacent client/user tests, full unit tests, lint, format, type, pyright, and whitespace gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Negative retained recipient IDs fail before login, request construction, action-status parsing, or diagnostic formatting. | `test_send_rejects_negative_user_recipient_id_before_login` failed RED for `-1` and `-100`, then passed GREEN after recipient ID range validation was added. | Calling `login_check()`, sending `DashboardMessageAction`, submitting negative `to_user_id`, or raising post-request status errors rejects this local completion claim. | `PrivateMessage.send(...)` recipient preflight | `src/wikidot/module/private_message.py`, `tests/unit/test_private_message.py` |
| R2 | Valid zero recipient IDs remain valid send payload values. | `test_send_accepts_zero_recipient_id` passed RED and GREEN, asserting the request payload uses `to_user_id == 0`. | Rejecting zero, converting it to `None`, stringifying it unexpectedly, or changing valid send payload shape rejects this local completion claim. | `PrivateMessage.send(...)` request payload | `tests/unit/test_private_message.py` |
| R3 | Existing send behavior and adjacent workflows remain green. | `TestPrivateMessage` passed 55 tests, `tests/unit/test_private_message.py` passed 151 tests, adjacent client/user coverage passed 328 tests, and full unit coverage passed 3379 tests. | Regressing recipient type validation, integer/bool validation, recipient name validation, recipient client validation, subject/body validation, action-status diagnostics, private-message accessors, user constructor behavior, or any unit test rejects this local completion claim. | Private-message send and adjacent workflows | `tests/unit` |
| R4 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level tests only with synthetic recipients and safe message literals. | Using credentials, cookies, auth JSON, private recipient names, private message bodies/subjects, raw rollout paths, live Wikidot actions, pushes, upstream Issues, or upstream PRs rejects this local completion claim. | Test and draft privacy | this draft |
| R5 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN, private-message/adjacent/full-unit tests, ruff, format check, mypy, temporary pyright, and `git diff --check` passed. | Test, lint, format, type, pyright, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `60d37ab fix(private_message): validate send recipient id range`.

- RED: `uv run pytest tests/unit/test_private_message.py::TestPrivateMessage -k recipient_id -q` selected 3 tests; 2 negative retained-recipient-ID cases failed before the fix by reaching mocked AMC/status handling and raising `WikidotStatusCodeException`, while 1 zero-ID compatibility guard passed.
- GREEN: the same focused command passed 3 tests after recipient ID range validation was added.
- `uv run ruff format src/wikidot/module/private_message.py tests/unit/test_private_message.py` left 2 files unchanged.
- `uv run pytest tests/unit/test_private_message.py::TestPrivateMessage -q` passed 55 tests.
- `uv run pytest tests/unit/test_private_message.py -q` passed 151 tests.
- `uv run pytest tests/unit/test_private_message.py tests/unit/test_client.py tests/unit/test_client_accessors.py tests/unit/test_user.py -q` passed 328 tests.
- `uv run pytest tests/unit -q` passed 3379 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `git diff --check` passed.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run --with pyright pyright` passed with 0 errors, 0 warnings, and 0 informations.

## Acceptance Criteria

- `PrivateMessage.send(...)` raises `ValueError("recipient.id must be non-negative")` when the recipient user's retained `id` is `-1` or `-100`.
- Negative retained recipient IDs fail before `client.login_check()`, `client.amc_client.request(...)`, returned action-status parsing, or recipient-based send diagnostics.
- Valid retained recipient ID `0` still produces a request payload with `to_user_id == 0`.
- Existing non-`User` recipient validation, malformed recipient ID type validation, malformed recipient name validation, recipient client ownership validation, subject/body validation, valid sends, returned send action-status validation, client private-message accessor behavior, private-message reads, and user constructor behavior remain green.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private recipient data, private message bodies/subjects, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.
- Private-data and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: Rehydrated users with negative retained IDs now fail before private-message sends. Mitigation: negative user IDs are impossible identity state; deterministic local validation is safer than invalid mutation payloads.
- Risk: Valid zero IDs could be accidentally rejected if validation were changed to positive-only. Mitigation: the focused zero-ID guard asserts `to_user_id == 0`.
- Risk: Validation precedence could regress earlier recipient diagnostics. Mitigation: the new range check runs after the existing integer/non-boolean ID type check and before recipient name/client/login work; the existing private-message and adjacent tests remain green.

## Dependencies

- Existing `User` constructor validation remains unchanged.
- Existing private-message send text validation, recipient object validation, recipient ID type validation, recipient name validation, recipient client validation, action-status validation, and client accessor delegation remain unchanged.

## Open Questions

None for this local slice. Remaining useful work should continue with fresh duplicate-checked public input boundaries, parser diagnostics, result ergonomics, action/read boundaries, retained cache/collection state, downstream mutable user-state preflights, or complexity candidates outside this now-covered private-message recipient-ID range boundary.

## Upstream-Safe Motivation

Private-message sends route Wikidot's `DashboardMessageAction` mutation through the recipient user's retained ID. That ID should satisfy the same non-negative identity contract before it leaves local state, even if a valid `User` was later mutated or rehydrated. Validating stored recipient identity prevents corrupted fixtures or generated records from becoming invalid mutation payloads while preserving zero-ID compatibility, valid sends, recipient client checks, text validation, and returned action-status diagnostics.

## Local Evidence, Not For Upstream Paste

- Local rollout-backed work established private-message sends as a practical workflow through action-status validation, text input validation, recipient input validation, recipient client validation, and adjacent private-message fetch/parse hardening.
- Existing local drafts covered non-`User` recipients, malformed recipient ID types, malformed recipient names, recipient client mismatch, direct user constructor ID ranges, QuickModule user IDs, and private-message record IDs; they did not validate negative retained `User.id` values at the send action boundary.
- The focused RED failure showed negative retained recipient IDs reached mocked send handling and action-status diagnostics instead of deterministic recipient-ID diagnostics. The GREEN regressions cover negative rejection, zero-ID compatibility, send behavior, adjacent client/user workflows, and full unit compatibility.
- This slice only validates retained recipient IDs at the private-message send boundary. It does not change private-message detail parsing, inbox/sentbox acquisition, direct message IDs, user construction, profile lookup, live site behavior, pushes, upstream Issues, or upstream PRs.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, private message bodies, private message subjects, real recipient names, raw action responses, source text from real sites, and private site data out of upstream discussion.

## Additional Notes

The implementation intentionally extends the existing `_validate_private_message_recipient(...)` helper instead of adding a second send-only validation path. The helper already owns recipient object, ID type, and name preflight for send payload construction and diagnostics, so the range check belongs next to those field contracts.
