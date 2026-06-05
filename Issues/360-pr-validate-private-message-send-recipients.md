# PR Draft: Validate PrivateMessage.send Recipient Inputs

## Summary

`PrivateMessage.send(client, recipient, subject, body)` and `client.private_message.send(...)` document `recipient` as a `User`, but malformed caller-provided recipient values were not rejected at the public API boundary. A non-`User` value could pass text validation, run the login check, and then leak raw attribute errors such as `AttributeError: 'dict' object has no attribute 'id'` during `to_user_id` payload construction. A malformed `User` with `id=None`, `id=True`, or `name=None` could reach AMC request/status handling before any stable recipient validation failure.

This change validates the private-message send recipient before login checks or AMC request construction. Invalid values now raise `ValueError("recipient must be a User")`, `ValueError("recipient.id must be an integer")`, or `ValueError("recipient.name must be a string")`. Valid private-message sends, subject/body validation, login-required behavior, action-status diagnostics, client accessor delegation, request payload shape, and successful no-return behavior remain unchanged.

## Outcome

Private-message send callers now get deterministic Python-side preflight validation for malformed recipient inputs instead of login work, accidental AMC send attempts, raw attribute errors, or action-status errors built around invalid recipient metadata.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators using `PrivateMessage.send(...)` or `client.private_message.send(...)` for browser-free notifications, moderation messages, migration notices, workflow status messages, and audit-driven private communications.

## Current Evidence

Local rollout evidence repeatedly treats private-message send as a practical mutation surface. Existing drafts [037-pr-retry-private-message-fetches.md](037-pr-retry-private-message-fetches.md), [054-pr-deduplicate-private-message-detail-fetches.md](054-pr-deduplicate-private-message-detail-fetches.md), [067-pr-deduplicate-direct-private-message-fetches.md](067-pr-deduplicate-direct-private-message-fetches.md), [254-pr-private-message-send-action-status-context.md](254-pr-private-message-send-action-status-context.md), [321-pr-private-message-response-body-type-context.md](321-pr-private-message-response-body-type-context.md), and [355-pr-validate-private-message-send-text-inputs.md](355-pr-validate-private-message-send-text-inputs.md) establish private-message retrieval, parsing, and send actions as practical workflows.

Those prior slices are not duplicates. They covered fetch retry behavior, duplicate detail acquisition, detail parser context, response-body typing, returned send action-status validation, and send `subject`/`body` validation. They did not validate the public `recipient` input before login checks, `to_user_id` payload construction, AMC submission, or recipient-based action-status diagnostics. This slice follows the input-boundary pattern from [355-pr-validate-private-message-send-text-inputs.md](355-pr-validate-private-message-send-text-inputs.md), but applies it to private-message send recipient identity.

## Related Issue

Builds directly on [254-pr-private-message-send-action-status-context.md](254-pr-private-message-send-action-status-context.md) and [355-pr-validate-private-message-send-text-inputs.md](355-pr-validate-private-message-send-text-inputs.md).

No upstream issue was filed from this local workspace.

## Changes

- Validate `recipient` is a `User` before login checks or dashboard message action requests.
- Validate `recipient.id` is a non-boolean integer before using it as `to_user_id`.
- Validate `recipient.name` is a string before it can appear in send action-status diagnostics.
- Keep `subject` and `body` preflight validation before login checks.
- Preserve successful `DashboardMessageAction` payload shape, recipient ID submission, subject/body submission, returned action-status validation, explicit non-`ok` status handling, and no-return successful sends.

## Type Of Change

- Input validation
- Public API behavior hardening
- Private-message send preflight safety
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `PrivateMessage.send(..., recipient=...)` must reject non-`User` recipient values with `ValueError("recipient must be a User")` before login checks or AMC requests. |
| R2 | `PrivateMessage.send(..., recipient=User(id=None or bool, ...))` must reject invalid recipient IDs with `ValueError("recipient.id must be an integer")` before login checks or AMC requests. |
| R3 | `PrivateMessage.send(..., recipient=User(name=None, ...))` must reject invalid recipient names with `ValueError("recipient.name must be a string")` before login checks or AMC requests. |
| R4 | `client.private_message.send(...)` must reach the same recipient validation path for malformed recipients. |
| R5 | Valid private-message sends, subject/body validation, login-required behavior, action-status diagnostics, client accessor delegation, and request payload shape must remain unchanged. |
| R6 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private message bodies/subjects, private recipient data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R7 | Focused RED/GREEN, adjacent private-message/client tests, full unit tests, lint, format, type, and whitespace gates must pass before claiming this local implementation complete; unavailable tools must be reported instead of hidden. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Non-`User` recipients fail before login or AMC request work. | `TestPrivateMessage.test_send_rejects_non_user_recipient_before_login` failed RED before the fix with raw `AttributeError`, then passed GREEN after validation was added. | Calling `client.login_check()`, calling `client.amc_client.request(...)`, coercing dicts/mocks into recipients, or leaking attribute errors rejects this local completion claim. | Private-message send preflight | `src/wikidot/module/private_message.py`, `tests/unit/test_private_message.py` |
| R2 | `User` recipients without a real integer ID fail before login or AMC request work. | `TestPrivateMessage.test_send_rejects_malformed_user_recipient_before_login` failed RED for `id=None` and `id=True` by reaching AMC/status handling, then passed GREEN after ID validation was added. | Submitting `to_user_id=None`, submitting `to_user_id=True`, treating bool as an integer user ID, or raising post-request status errors rejects this local completion claim. | Recipient ID preflight | `src/wikidot/module/private_message.py`, `tests/unit/test_private_message.py` |
| R3 | `User` recipients without a string name fail before login or AMC request work. | `TestPrivateMessage.test_send_rejects_malformed_user_recipient_before_login` failed RED for `name=None` by reaching AMC/status handling, then passed GREEN after name validation was added. | Building action-status diagnostics around `recipient.name=None`, calling login, or calling AMC rejects this local completion claim. | Recipient diagnostic preflight | `src/wikidot/module/private_message.py`, `tests/unit/test_private_message.py` |
| R4 | Client accessor sends use the same recipient validation path. | `TestClientPrivateMessageAccessor.test_send_message_rejects_non_user_recipient` passed through the real send implementation and asserts login is not called. | Mock-only coverage, bypassing `PrivateMessage.send(...)`, or letting accessor sends reach login with malformed recipients rejects this local completion claim. | Client private-message accessor | `src/wikidot/module/client.py`, `tests/unit/test_client.py` |
| R5 | Valid sends and existing send diagnostics remain unchanged. | Focused GREEN included `test_send_success`; the adjacent private-message/client run passed 57 tests; the full unit suite passed 978 tests. | Regressing login-required behavior for valid inputs, `DashboardMessageAction`, `event=send`, `to_user_id`, `subject`, `source`, missing-status diagnostics, explicit non-`ok` status handling, inbox/sentbox accessors, or direct message reads rejects this local completion claim. | Private-message workflow | `tests/unit/test_private_message.py`, `tests/unit/test_client.py` |
| R6 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level tests only with synthetic recipients and no message content from real Wikidot. | Using real recipient names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, raw action responses, private message bodies, private message subjects, or private recipient data rejects this local completion claim. | Test and draft privacy | this draft |
| R7 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, adjacent tests passed, full unit passed, ruff, format, mypy, and whitespace checks passed; pyright was unavailable. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `cafdae8 fix(private_message): validate send recipients`.

- RED: `.venv/bin/python -m pytest -q tests/unit/test_private_message.py::TestPrivateMessage::test_send_rejects_non_user_recipient_before_login` failed before the fix with raw `AttributeError: 'dict' object has no attribute 'id'`.
- RED: `.venv/bin/python -m pytest -q tests/unit/test_private_message.py::TestPrivateMessage::test_send_rejects_malformed_user_recipient_before_login` failed before the fix for malformed `User` fields by reaching AMC/status handling and raising `WikidotStatusCodeException`.
- GREEN: `.venv/bin/python -m pytest -q tests/unit/test_private_message.py::TestPrivateMessage::test_send_rejects_non_user_recipient_before_login tests/unit/test_private_message.py::TestPrivateMessage::test_send_rejects_malformed_user_recipient_before_login` passed 4 tests.
- GREEN: `.venv/bin/python -m pytest -q tests/unit/test_private_message.py::TestPrivateMessage::test_send_success tests/unit/test_private_message.py::TestPrivateMessage::test_send_rejects_non_user_recipient_before_login tests/unit/test_private_message.py::TestPrivateMessage::test_send_rejects_malformed_user_recipient_before_login tests/unit/test_client.py::TestClientPrivateMessageAccessor::test_send_message_rejects_non_user_recipient` passed 6 tests.
- `.venv/bin/python -m pytest -q tests/unit/test_private_message.py tests/unit/test_client.py::TestClientPrivateMessageAccessor` passed 57 tests.
- `.venv/bin/python -m pytest -q tests/unit` passed 978 tests.
- `ruff check .` passed.
- `ruff format --check .` passed with 81 files already formatted.
- `.venv/bin/mypy src tests` passed with no issues in 81 source files.
- `git diff --check` passed.

Not run successfully: `pyright src tests` was unavailable because neither `.venv/bin/pyright` nor a PATH `pyright` executable existed in this environment.

## Acceptance Criteria

- `PrivateMessage.send(client, {"id": 12345, "name": "test-user"}, "Subject", "Body")` raises `ValueError("recipient must be a User")` before `client.login_check()` or `client.amc_client.request(...)`.
- `PrivateMessage.send(client, User(client, id=None, name="test-user"), "Subject", "Body")` raises `ValueError("recipient.id must be an integer")` before login or AMC work.
- `PrivateMessage.send(client, User(client, id=True, name="test-user"), "Subject", "Body")` raises `ValueError("recipient.id must be an integer")` before login or AMC work.
- `PrivateMessage.send(client, User(client, id=12345, name=None), "Subject", "Body")` raises `ValueError("recipient.name must be a string")` before login or AMC work.
- `client.private_message.send(...)` reaches the same validation path for malformed recipients.
- Valid sends still call `client.login_check()` and still submit `DashboardMessageAction` with `event: "send"`, `to_user_id`, `subject`, and `source`.
- Existing subject/body validation, missing action-status diagnostics, explicit non-`ok` status handling, private-message detail parsing, inbox/sentbox acquisition, client accessors, and no-return successful sends remain unchanged.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private message bodies/subjects, private recipient data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

Private-message send is a non-retried mutation action. The recipient object supplies the remote `to_user_id` and the human-readable diagnostic name for returned action-status failures, so malformed recipient inputs should fail deterministically before login or AMC work. The change is narrow: it keeps valid send behavior and existing send response diagnostics unchanged while preventing accidental sends or misleading diagnostics from malformed caller-provided recipient values.

## Local Evidence, Not For Upstream Paste

- Local rollout evidence established private-message retrieval, parsing, and send actions as practical workflows.
- The focused RED failures showed malformed recipient values crossing into login, payload construction, and action-status handling instead of failing at the public call boundary.
- Existing private-message send drafts covered returned action-status validation and send text validation, but not malformed public `recipient` input preflight.
- This slice only validates private-message send recipient inputs. It does not change private-message detail parsing, inbox/sentbox acquisition, empty lookup behavior, send retry semantics, returned action-status validation, client authentication, live Wikidot behavior, or message dataclass fields.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, cookies, auth JSON, raw action responses, private message bodies, private message subjects, recipient names from real messages, page source text from real sites, and private site data out of upstream discussion.

## Additional Notes

The change intentionally rejects malformed values instead of coercing them. Callers that load private-message recipient IDs or names from JSON, YAML, CLI flags, generated structures, spreadsheets, or environment variables should resolve them into a real `User` object before calling wikidot.py private-message send helpers.
