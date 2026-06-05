# PR Draft: Validate PrivateMessage.send Text Inputs Before Login

## Summary

`PrivateMessage.send(client, recipient, subject, body)` documents `subject` and `body` as strings, but malformed non-string values were not rejected at the public API boundary. Because the method used `@login_required`, invalid values reached the login check before any stable input validation, and after login they could be placed into the dashboard message action payload and progress into returned action-status handling.

This change validates `subject` and `body` before login checks, dashboard message request construction, AMC submission, returned action-status parsing, or send-success acceptance. Invalid values now raise `ValueError("subject must be a string")` or `ValueError("body must be a string")`. Valid private-message sends, login-required behavior, action-status diagnostics, and request payload shape remain unchanged.

## Outcome

Browser-free private-message send callers now get deterministic Python-side preflight validation for malformed message text fields instead of login work, remote send attempts, or downstream action-status errors.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators using `PrivateMessage.send(...)` or the client private-message accessor for browser-free notifications, moderation messages, workflow status messages, migration notices, or audit-driven private communications.

## Current Evidence

Local rollout evidence repeatedly treats private messages as practical read and write surfaces. Existing drafts [037-pr-retry-private-message-fetches.md](037-pr-retry-private-message-fetches.md), [054-pr-deduplicate-private-message-detail-fetches.md](054-pr-deduplicate-private-message-detail-fetches.md), [067-pr-deduplicate-direct-private-message-fetches.md](067-pr-deduplicate-direct-private-message-fetches.md), [073-pr-reuse-private-message-detail-parsing.md](073-pr-reuse-private-message-detail-parsing.md), [077-pr-skip-empty-private-message-fetch-batches.md](077-pr-skip-empty-private-message-fetch-batches.md), [119-pr-preserve-private-message-subject-spacing.md](119-pr-preserve-private-message-subject-spacing.md), [254-pr-private-message-send-action-status-context.md](254-pr-private-message-send-action-status-context.md), [273-pr-private-message-detail-subject-body-context.md](273-pr-private-message-detail-subject-body-context.md), and [321-pr-private-message-response-body-type-context.md](321-pr-private-message-response-body-type-context.md) establish private-message detail/list acquisition, subject/body parsing, empty lookup behavior, and send action-status validation as practical surfaces.

Those prior slices are not duplicates. They covered read-side retry/deduplication/parsing/response-body behavior and returned send action-status confirmation after a remote send action. They did not validate public send `subject`/`body` inputs before login checks or request construction. This slice follows the input-boundary pattern from [350-pr-validate-page-text-inputs.md](350-pr-validate-page-text-inputs.md) and [354-pr-validate-forum-write-text-inputs.md](354-pr-validate-forum-write-text-inputs.md), but applies it to private-message sends.

## Related Issue

Builds directly on [254-pr-private-message-send-action-status-context.md](254-pr-private-message-send-action-status-context.md), [350-pr-validate-page-text-inputs.md](350-pr-validate-page-text-inputs.md), and [354-pr-validate-forum-write-text-inputs.md](354-pr-validate-forum-write-text-inputs.md).

No upstream issue was filed from this local workspace.

## Changes

- Validate `PrivateMessage.send(subject=...)` before login checks or dashboard message action requests.
- Validate `PrivateMessage.send(body=...)` before login checks or dashboard message action requests.
- Move the login check inside `PrivateMessage.send(...)` after validation so valid sends keep the same login-required behavior while invalid text fields fail earlier.
- Reuse the private module text-field validator already added for forum write inputs.
- Preserve successful `DashboardMessageAction` payload shape, recipient ID submission, subject/body submission, returned action-status validation, explicit non-`ok` status handling, and no-return successful sends.

## Type Of Change

- Input validation
- Public API behavior hardening
- Private-message send preflight safety
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `PrivateMessage.send(..., subject=...)` must reject non-string subject values with `ValueError("subject must be a string")` before login checks or AMC requests. |
| R2 | `PrivateMessage.send(..., body=...)` must reject non-string body values with `ValueError("body must be a string")` before login checks or AMC requests. |
| R3 | Valid private-message sends must keep the existing login-required behavior and request payload shape. |
| R4 | Existing missing action-status and explicit non-`ok` action-status diagnostics must remain unchanged for valid text inputs. |
| R5 | Adjacent private-message read APIs and client private-message accessors must remain unchanged. |
| R6 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R7 | Focused RED/GREEN, adjacent private-message/client tests, full unit tests, lint, format, type, and whitespace gates must pass before claiming this local implementation complete; unavailable tools must be reported instead of hidden. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Non-string subjects fail before side effects. | `TestPrivateMessage.test_send_rejects_non_string_text_inputs_before_login[subject]` failed RED before the fix because the invalid value reached action-status handling, then passed GREEN after validation was added. | Calling `login_check()`, calling `amc_client.request(...)`, or leaking action-status exceptions rejects this local completion claim. | Private-message send preflight | `src/wikidot/module/private_message.py`, `tests/unit/test_private_message.py` |
| R2 | Non-string bodies fail before side effects. | `TestPrivateMessage.test_send_rejects_non_string_text_inputs_before_login[body]` failed RED before the fix because the invalid value reached action-status handling, then passed GREEN after validation was added. | Calling `login_check()`, calling `amc_client.request(...)`, or leaking action-status exceptions rejects this local completion claim. | Private-message send preflight | `src/wikidot/module/private_message.py`, `tests/unit/test_private_message.py` |
| R3 | Valid send behavior remains unchanged. | Focused GREEN included `test_send_requires_login` and `test_send_success`; adjacent private-message/client accessor tests passed 52 tests. | Losing the login-required exception for valid inputs, changing `DashboardMessageAction`, changing `event=send`, changing `to_user_id`, changing subject/body payload fields, or returning a new value rejects this local completion claim. | Private-message send behavior | `tests/unit/test_private_message.py`, `tests/unit/test_client.py` |
| R4 | Existing action-status diagnostics remain unchanged. | Focused GREEN included missing action-status and explicit non-`ok` status tests. | Accepting missing status, changing recipient/event/field context, swallowing non-`ok` statuses, or reclassifying non-`ok` statuses as `ValueError` rejects this local completion claim. | Private-message send response boundary | `tests/unit/test_private_message.py` |
| R5 | Private-message reads and accessors remain green. | `tests/unit/test_private_message.py` plus `TestClientPrivateMessageAccessor` passed 52 tests; the full unit suite passed 963 tests. | Regressing inbox/sentbox acquisition, direct detail reads, private-message parsing, empty lookup behavior, or client accessor delegation rejects this local completion claim. | Private-message module and client accessor | affected private-message/client tests |
| R6 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level tests only. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, raw action responses, private message bodies, private message subjects, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R7 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, adjacent private-message/client tests passed, full unit passed, ruff, format, mypy, and whitespace checks passed; pyright was unavailable. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `25b97b9 fix(private_message): validate send text inputs`.

- RED: `PYTHONPATH=src pytest -q tests/unit/test_private_message.py::TestPrivateMessage::test_send_rejects_non_string_text_inputs_before_login` failed 2 parameterized cases before the fix because invalid `subject` and `body` values reached login/action-status work instead of raising stable `ValueError`.
- GREEN: `PYTHONPATH=src pytest -q tests/unit/test_private_message.py::TestPrivateMessage::test_send_rejects_non_string_text_inputs_before_login tests/unit/test_private_message.py::TestPrivateMessage::test_send_requires_login tests/unit/test_private_message.py::TestPrivateMessage::test_send_success tests/unit/test_private_message.py::TestPrivateMessage::test_send_missing_action_status_includes_recipient_event_and_field_context tests/unit/test_private_message.py::TestPrivateMessage::test_send_explicit_non_ok_action_status_raises_status_exception` passed 6 tests.
- `PYTHONPATH=src pytest -q tests/unit/test_private_message.py tests/unit/test_client.py::TestClientPrivateMessageAccessor` passed 52 tests.
- `ruff format src/wikidot/module/private_message.py tests/unit/test_private_message.py` left 2 files unchanged.
- `ruff check src/wikidot/module/private_message.py tests/unit/test_private_message.py` passed.
- `.venv/bin/mypy src tests` passed with no issues in 81 source files.
- `.venv/bin/python -m pytest -q tests/unit` passed 963 tests.
- `ruff check .` passed.
- `ruff format --check .` passed with 81 files already formatted.
- `git diff --check` passed.

Not run successfully: `pyright src tests` was unavailable because neither `.venv/bin/pyright` nor a PATH `pyright` executable existed in this environment.

## Acceptance Criteria

- `PrivateMessage.send(client, recipient, subject=3, body="Body")` raises `ValueError("subject must be a string")` before calling `client.login_check()` or `client.amc_client.request(...)`.
- `PrivateMessage.send(client, recipient, subject="Subject", body=3)` raises `ValueError("body must be a string")` before calling `client.login_check()` or `client.amc_client.request(...)`.
- Valid sends still call `client.login_check()` and still submit `DashboardMessageAction` with `event: "send"`, `to_user_id`, `subject`, and `source`.
- Logged-out valid sends still raise `LoginRequiredException`.
- Missing returned send action status still raises contextual `NoElementException`.
- Explicit non-`ok` send action status still raises `WikidotStatusCodeException`.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

Private-message sends are non-retried mutation actions. Runtime validation should reject malformed subject/body payloads before login checks or request construction, so caller configuration errors cannot trigger remote send work or confusing downstream action-status failures. The change is narrow: it keeps valid send semantics and existing action-status diagnostics unchanged.

## Local Evidence, Not For Upstream Paste

- Local rollout evidence established private-message reads, detail parsing, subject/body handling, send action-status validation, and client private-message accessor behavior as practical surfaces.
- The focused RED failures showed malformed send text inputs crossing into login/action-status work instead of failing at the public call boundary.
- Existing private-message drafts covered read-side parsing and returned send action-status validation, but not malformed public `PrivateMessage.send(subject=..., body=...)` inputs.
- This slice only validates private-message send text inputs. It does not change private-message detail parsing, inbox/sentbox acquisition, empty lookup behavior, client accessor delegation, send retry semantics, returned action-status validation, or live Wikidot behavior.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw action response bodies, private message bodies, private message subjects, page source text from real sites, and private site data out of upstream discussion.

## Additional Notes

The change intentionally rejects malformed values instead of coercing them. Callers that load private-message subjects or bodies from JSON, YAML, CLI flags, generated structures, spreadsheets, or environment variables should normalize them to strings before calling `PrivateMessage.send(...)`.
