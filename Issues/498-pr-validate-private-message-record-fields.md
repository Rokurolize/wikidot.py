# PR Draft: Validate PrivateMessage Record Fields

## Summary

`PrivateMessage` records are produced by direct private-message detail reads, inbox/sent-box acquisition, `Client.private_message` accessors, duplicate-detail reuse, generated PM ledgers, and local fixtures. Earlier local slices validated lookup IDs, loaded-collection search IDs, collection constructor entries, retry controls, parser diagnostics, response bodies, and the stored message ID field. One direct record-state gap remained: the public `PrivateMessage(...)` constructor still accepted malformed `sender`, `recipient`, `subject`, `body`, and `created_at` values.

This change validates the remaining `PrivateMessage` record fields at initialization. `sender` and `recipient` must be `AbstractUser` instances, `subject` and `body` must be strings, and `created_at` must be a `datetime`. Invalid values now raise deterministic `ValueError` messages before malformed record state can be stored, while valid parsed messages, direct reads, inbox/sent-box acquisition, duplicate-detail reuse, collection behavior, `from_id(...)`, and send behavior remain unchanged.

## Outcome

Callers cannot silently construct private-message records with malformed participant, text, or timestamp state, while existing private-message read and send workflows continue to work.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use browser-free private-message detail reads, inbox/sent-box acquisition, generated PM audit ledgers, private-message migration checks, `Client.private_message.get_message(...)`, `Client.private_message.get_messages(...)`, or local fixtures that construct `PrivateMessage` records directly.

## Current Evidence

Private-message drafts [037-pr-retry-private-message-fetches.md](037-pr-retry-private-message-fetches.md), [054-pr-deduplicate-private-message-detail-fetches.md](054-pr-deduplicate-private-message-detail-fetches.md), [067-pr-deduplicate-direct-private-message-fetches.md](067-pr-deduplicate-direct-private-message-fetches.md), [073-pr-reuse-private-message-detail-parsing.md](073-pr-reuse-private-message-detail-parsing.md), [077-pr-skip-empty-private-message-fetch-batches.md](077-pr-skip-empty-private-message-fetch-batches.md), [106-pr-preserve-private-message-body-spacing.md](106-pr-preserve-private-message-body-spacing.md), [119-pr-preserve-private-message-subject-spacing.md](119-pr-preserve-private-message-subject-spacing.md), [206-pr-private-message-detail-response-body-context.md](206-pr-private-message-detail-response-body-context.md), [207-pr-private-message-list-response-body-context.md](207-pr-private-message-list-response-body-context.md), [272-pr-private-message-detail-timestamp-context.md](272-pr-private-message-detail-timestamp-context.md), [273-pr-private-message-detail-subject-body-context.md](273-pr-private-message-detail-subject-body-context.md), [287-pr-private-message-detail-timestamp-value-context.md](287-pr-private-message-detail-timestamp-value-context.md), [288-pr-private-message-detail-user-context.md](288-pr-private-message-detail-user-context.md), [321-pr-private-message-response-body-type-context.md](321-pr-private-message-response-body-type-context.md), [355-pr-validate-private-message-send-text-inputs.md](355-pr-validate-private-message-send-text-inputs.md), [360-pr-validate-private-message-send-recipients.md](360-pr-validate-private-message-send-recipients.md), [361-pr-validate-private-message-message-id-inputs.md](361-pr-validate-private-message-message-id-inputs.md), [381-pr-validate-private-message-find-id.md](381-pr-validate-private-message-find-id.md), [397-pr-validate-private-message-retry-controls.md](397-pr-validate-private-message-retry-controls.md), [425-pr-validate-private-message-collection-initialization.md](425-pr-validate-private-message-collection-initialization.md), and [451-pr-validate-private-message-id-field.md](451-pr-validate-private-message-id-field.md) establish private-message reads, sends, parser boundaries, request inputs, loaded collection lookup, collection construction, retry controls, and the stored ID field as practical operational surfaces.

Adjacent constructor-hardening drafts [458-pr-validate-forum-thread-creator-time-fields.md](458-pr-validate-forum-thread-creator-time-fields.md), [459-pr-validate-forum-post-creator-time-fields.md](459-pr-validate-forum-post-creator-time-fields.md), [460-pr-validate-forum-post-identity-text-fields.md](460-pr-validate-forum-post-identity-text-fields.md), [464-pr-validate-forum-post-revision-creator-time-fields.md](464-pr-validate-forum-post-revision-creator-time-fields.md), [467-pr-validate-page-revision-creator-time-fields.md](467-pr-validate-page-revision-creator-time-fields.md), and [495-pr-validate-user-scalar-fields.md](495-pr-validate-user-scalar-fields.md) establish the local pattern for validating direct dataclass record state instead of relying only on parser boundaries.

## Related Issue / Non-Duplicate Analysis

This is not a duplicate of Issue 451. Issue 451 validates only `PrivateMessage.id`; this slice validates the remaining direct record fields.

This is not a duplicate of Issues 272, 273, 287, or 288. Those slices cover malformed generated markup at the parser boundary. This slice covers direct `PrivateMessage(...)` construction used by fixtures, generated ledgers, rehydrated records, and tests after parser output has already become field values.

This is not a duplicate of Issues 355 or 360. Those slices validate send-action inputs before a mutation request. This slice validates stored message records and accepts any `AbstractUser`, preserving parsed regular, deleted, anonymous, guest, and system users.

No upstream issue was filed from this local workspace.

## Changes

- Add `_validate_private_message_user(...)` for stored sender and recipient fields.
- Add `_validate_private_message_created_at(...)` for stored creation timestamps.
- Reuse `validate_text_field(...)` for stored `subject` and `body` fields.
- Update `PrivateMessage.__post_init__` to validate `id`, `sender`, `recipient`, `subject`, `body`, and `created_at`.
- Update private-message parser tests that mocked `user_parser` with bare `MagicMock` return values so successful parse paths now use valid `User` fixtures.
- Add focused constructor regressions for malformed sender/recipient values, subject/body values, and created timestamps.

## Type Of Change

- Input validation
- Public dataclass constructor behavior hardening
- Private-message record state integrity
- Test addition
- Test fixture cleanup

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `PrivateMessage(sender=...)` and `PrivateMessage(recipient=...)` must reject non-`AbstractUser` values with field-specific `ValueError` messages. |
| R2 | `PrivateMessage(subject=...)` and `PrivateMessage(body=...)` must reject non-string values with `ValueError("subject must be a string")` or `ValueError("body must be a string")`. |
| R3 | `PrivateMessage(created_at=...)` must reject non-`datetime` values with `ValueError("created_at must be a datetime")`. |
| R4 | Valid parsed private-message reads, inbox/sent-box acquisition, duplicate-detail reuse, collection behavior, `PrivateMessage.from_id(...)`, client accessors, send behavior, parser diagnostics, and retry behavior must remain unchanged. |
| R5 | Focused RED/GREEN, private-message tests, full unit tests, lint, format, mypy, pyright, and whitespace gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Malformed constructor participant values fail at the public dataclass boundary. | `TestPrivateMessage.test_init_rejects_malformed_message_users` failed RED for 6 malformed sender/recipient cases, then passed GREEN after validation was added. | Accepting missing values, booleans, dictionaries, mocks, or arbitrary objects as stored participants rejects this local completion claim. | PrivateMessage constructor | `src/wikidot/module/private_message.py`, `tests/unit/test_private_message.py` |
| R2 | Malformed constructor text values fail before record state is stored. | `TestPrivateMessage.test_init_rejects_malformed_message_text_fields` failed RED for 6 malformed subject/body cases, then passed GREEN after text validation was added. | Coercing text values, storing non-strings, or weakening send text validation rejects this local completion claim. | PrivateMessage constructor | `src/wikidot/module/private_message.py`, `tests/unit/test_private_message.py` |
| R3 | Malformed constructor timestamps fail before record state is stored. | `TestPrivateMessage.test_init_rejects_malformed_created_at` failed RED for 5 malformed timestamp cases, then passed GREEN after timestamp validation was added. | Accepting missing values, booleans, epoch integers, date strings, lists, or arbitrary timestamp objects rejects this local completion claim. | PrivateMessage constructor | `src/wikidot/module/private_message.py`, `tests/unit/test_private_message.py` |
| R4 | Existing private-message workflows remain green with valid parser-created users and timestamps. | `tests/unit/test_private_message.py` passed 107 tests after old bare parser mocks were replaced with valid user fixtures. | Regressing direct reads, empty direct reads, inbox acquisition, sent-box acquisition, duplicate detail behavior, parser diagnostics, collection initialization, loaded-collection lookup, `PrivateMessage.from_id(...)`, client accessors, send behavior, or retry controls rejects this local completion claim. | Private-message workflows | `tests/unit/test_private_message.py` |
| R5 | Repository quality gates pass in the local dependency environment. | Full ruff, format, mypy, pyright, unit, and whitespace checks passed. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `33618be fix(private_message): validate record fields`.

- RED: `uv run pytest tests/unit/test_private_message.py::TestPrivateMessage::test_init_rejects_malformed_message_users tests/unit/test_private_message.py::TestPrivateMessage::test_init_rejects_malformed_message_text_fields tests/unit/test_private_message.py::TestPrivateMessage::test_init_rejects_malformed_created_at -q` failed 17 tests before the fix; every malformed participant, text, or timestamp value reported `DID NOT RAISE`.
- GREEN: `uv run pytest tests/unit/test_private_message.py::TestPrivateMessage::test_str_representation tests/unit/test_private_message.py::TestPrivateMessage::test_init_rejects_non_integer_message_id tests/unit/test_private_message.py::TestPrivateMessage::test_init_rejects_malformed_message_users tests/unit/test_private_message.py::TestPrivateMessage::test_init_rejects_malformed_message_text_fields tests/unit/test_private_message.py::TestPrivateMessage::test_init_rejects_malformed_created_at -q` passed 22 tests.
- `uv run pytest tests/unit/test_private_message.py -q` passed 107 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 86 files already formatted.
- `uv run mypy src tests` passed with no issues in 86 source files.
- `uv run pyright src tests` passed with 0 errors, 0 warnings, and 0 informations.
- `uv run pytest tests/unit -q` passed 2203 tests.
- `git diff --check` passed.

## Acceptance Criteria

- `PrivateMessage(sender=None)`, `True`, and `{"id": 12345}` raise `ValueError("sender must be an AbstractUser")` when every other constructor field is valid.
- `PrivateMessage(recipient=None)`, `True`, and `{"id": 12345}` raise `ValueError("recipient must be an AbstractUser")` when every other constructor field is valid.
- `PrivateMessage(subject=None)`, `True`, and `123` raise `ValueError("subject must be a string")`.
- `PrivateMessage(body=None)`, `True`, and `123` raise `ValueError("body must be a string")`.
- `PrivateMessage(created_at=None)`, `True`, `1700000000`, `"2023-01-01"`, and `[]` raise `ValueError("created_at must be a datetime")`.
- Existing direct PM reads, inbox/sent-box acquisition, collection initialization, loaded-collection lookup, `PrivateMessage.from_id(...)`, client private-message accessors, parser diagnostics, retry behavior, duplicate reuse, and send behavior remain green.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private message bodies, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Risks And Mitigations

- Risk: Successful parser tests that used bare mocks could hide the new invariant. Mitigation: successful parse fixtures now return real `User` instances so tests exercise the same valid record shape as production parser output.
- Risk: Rejecting non-`AbstractUser` participants could be confused with send-recipient validation. Mitigation: send remains stricter and requires `User`; stored private-message records accept `AbstractUser` so deleted, anonymous, guest, and system users remain representable.
- Risk: Constructor validation could be mistaken for parser diagnostics. Mitigation: parser-boundary diagnostics remain covered separately and unchanged; this slice validates only stored field values.

## Dependencies

- Private-message parser output must continue to produce `AbstractUser` participants and `datetime` timestamps.
- Valid message subjects and bodies are represented as strings.
- Existing `validate_text_field(...)` semantics remain the shared text-field guard.

## Open Questions

None for this local slice. Future work can separately evaluate whether empty subject/body strings should be constrained, but that would be a semantic policy change beyond this scalar type guard.

## Upstream-Safe Motivation

`PrivateMessage` is the record shape behind browser-free PM reads, inbox/sent-box acquisition, client accessors, duplicate-detail reuse, and generated PM ledgers. Parser paths already produce typed participants, text, and timestamps or fail with contextual diagnostics. Constructor validation keeps malformed local metadata out of fixtures, generated ledgers, migration comparisons, message summaries, and downstream audit tooling while preserving valid Wikidot-derived records.

## Local Evidence, Not For Upstream Paste

- Local rollout-backed work repeatedly used browser-free private-message detail reads, inbox/sent-box acquisition, duplicate-detail reuse, empty direct lookup handling, client accessors, and tests that seed private-message records directly.
- Existing local drafts covered private-message fetch retry behavior, duplicate detail reduction, parse reuse, response diagnostics, parser field diagnostics, send inputs, message ID input validation, loaded collection search validation, collection constructor validation, retry-control validation, and direct ID-field validation, but did not cover direct `PrivateMessage(sender=..., recipient=..., subject=..., body=..., created_at=...)` construction.
- The focused RED failures showed invalid constructor participants, text values, and timestamps were accepted as dataclass state. The GREEN regressions cover missing values, booleans, dictionaries, integers, strings, date strings, epoch integers, and list values.
- This slice only validates stored private-message record fields at construction. It does not change direct PM acquisition, inbox/sent-box acquisition, parser selectors, message ID parsing, cached duplicate behavior, collection initialization, `find(...)`, `PrivateMessage.from_id(...)`, `PrivateMessage.send(...)`, live site behavior, or parsing policy.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw login response bodies, private message bodies, page source text, forum source text, and private site data out of upstream discussion.

## Additional Notes

The change intentionally rejects malformed values instead of coercing them. Callers that load private-message records from JSON, YAML, CLI flags, generated structures, spreadsheets, or environment variables should normalize participant records, text fields, and timestamps before constructing `PrivateMessage` objects.
