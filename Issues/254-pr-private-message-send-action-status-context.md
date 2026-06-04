# PR Draft: Validate PrivateMessage.send Action Status Before Accepting Send Success

## Summary

`PrivateMessage.send(...)` sends Wikidot's dashboard message action with `event: "send"` and previously discarded the returned action response. Because the lower-level AMC connector only raises for non-`ok` statuses when the `status` field is present, a decoded response without `status` could be accepted as a successful private-message send.

This follow-up validates the returned send action status inside `PrivateMessage.send(...)`. A missing `status` raises `NoElementException` with recipient, recipient ID, event, and field context. Explicit non-`ok` statuses raise `WikidotStatusCodeException`. Successful `status: ok` sends and request payload construction remain unchanged.

## Related Issue

Builds on the private-message workflow drafts [037-pr-retry-private-message-fetches.md](037-pr-retry-private-message-fetches.md) and [077-pr-skip-empty-private-message-fetch-batches.md](077-pr-skip-empty-private-message-fetch-batches.md), which intentionally left the direct send action unchanged while improving message fetch paths. It also follows the non-retried mutation action-status pattern established by [250-pr-forum-post-edit-action-status-context.md](250-pr-forum-post-edit-action-status-context.md), [251-pr-forum-thread-reply-action-status-context.md](251-pr-forum-thread-reply-action-status-context.md), [252-pr-forum-category-create-thread-action-status-context.md](252-pr-forum-category-create-thread-action-status-context.md), and [253-pr-site-invite-action-status-context.md](253-pr-site-invite-action-status-context.md).

No upstream issue was filed from this local workspace.

## Changes

- Validate the returned dashboard message send action response before treating `PrivateMessage.send(...)` as successful.
- Convert a missing send action `status` into `NoElementException` with recipient name, recipient ID, event, and field context.
- Preserve explicit non-`ok` status handling through `WikidotStatusCodeException`.
- Add focused public-interface regressions for malformed and explicit non-`ok` private-message send responses.
- Preserve login checks, request payload construction, recipient ID submission, subject/body submission, and successful no-return behavior.

## Type Of Change

- Bug fix / diagnostics improvement
- Private-message send action response validation
- Test addition

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| A private-message send response missing `status` fails with contextual `NoElementException`. | `TestPrivateMessage.test_send_missing_action_status_includes_recipient_event_and_field_context` returns `{}` from the send action response and asserts `NoElementException`. | Treating the response as successful, raising a raw `KeyError`, or omitting send context rejects this local completion claim. |
| The malformed action-status message identifies recipient, recipient ID, event, and missing field. | The focused regression asserts `Private message send action response is malformed for recipient: test-user (id=12345, event=send, field=status)`. | Omitting recipient name, recipient ID, event, or field context makes the failure ambiguous and rejects this local completion claim. |
| Explicit non-`ok` send action statuses are not treated as successful sends. | `TestPrivateMessage.test_send_explicit_non_ok_action_status_raises_status_exception` returns `{"status": "not_ok"}` and asserts `WikidotStatusCodeException.status_code == "not_ok"`. | Returning successfully, swallowing the status, or reclassifying it as `NoElementException` rejects this local completion claim. |
| Successful send behavior remains unchanged. | `TestPrivateMessage.test_send_success` passes with `status: ok` and still asserts `DashboardMessageAction`, `send`, recipient ID, subject, and body payload fields. | Regressions in login checks, request payload shape, recipient ID submission, subject/body submission, or successful no-return behavior reject this local completion claim. |
| Adjacent private-message accessor behavior remains unchanged. | `uv run --extra test pytest tests/unit/test_private_message.py tests/unit/test_client.py::TestClientPrivateMessageAccessor -q` passed 43 tests. | Regressions in inbox/sentbox/get-message accessors or the client private-message send delegator reject this local completion claim. |
| Broad unit and static quality gates remain green. | `uv run --extra test pytest tests/unit -q`; `uv run ruff check`; `uv run ruff format --check`; `uv run mypy src tests`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject this local completion claim. |

## Testing

Implemented locally in commit `f81e038 fix(private_message): guard send action status`.

- RED: `uv run --extra test pytest tests/unit/test_private_message.py::TestPrivateMessage::test_send_missing_action_status_includes_recipient_event_and_field_context tests/unit/test_private_message.py::TestPrivateMessage::test_send_explicit_non_ok_action_status_raises_status_exception -q` failed before the fix with `Failed: DID NOT RAISE <class 'wikidot.common.exceptions.NoElementException'>` and `Failed: DID NOT RAISE <class 'wikidot.common.exceptions.WikidotStatusCodeException'>`.
- GREEN: `uv run --extra test pytest tests/unit/test_private_message.py::TestPrivateMessage::test_send_missing_action_status_includes_recipient_event_and_field_context tests/unit/test_private_message.py::TestPrivateMessage::test_send_explicit_non_ok_action_status_raises_status_exception -q` passed.
- `uv run --extra test pytest tests/unit/test_private_message.py::TestPrivateMessage -q` passed 6 tests.
- `uv run --extra test pytest tests/unit/test_private_message.py -q` passed 38 tests.
- `uv run --extra test pytest tests/unit/test_private_message.py tests/unit/test_client.py::TestClientPrivateMessageAccessor -q` passed 43 tests.
- `uv run --extra test pytest tests/unit -q` passed 805 tests.
- `uv run ruff check`.
- `uv run ruff format --check`.
- `git diff --check`.
- `uv run mypy src tests`.

Not run successfully: `uv run pyright --version` because this environment could not find a `pyright` executable.

## Acceptance Criteria

- `PrivateMessage.send(...)` raises `NoElementException` when the returned dashboard message send action response lacks `status`.
- The malformed-response message includes recipient name, recipient ID, action event, and missing field.
- Explicit non-`ok` send action statuses are not treated as successful sends.
- Successful send paths keep the existing login check, request payload shape, recipient ID submission, subject/body submission, and no-return behavior.
- No private message body, subject text, live Wikidot action, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Private-message sends are non-retried mutation actions. Callers should not accept an unclassified Wikidot response as proof that a message was sent merely because the response object decoded without crashing. Validating the returned action status makes `PrivateMessage.send(...)` consistent with nearby action-status guards and gives operators a compact recipient/event signal when Wikidot omits the required status field.

## Local Evidence, Not For Upstream Paste

- Earlier private-message drafts improved message fetch retries and empty-batch handling while explicitly leaving the direct send action path unchanged.
- Issues 250 through 253 established the adjacent action-status pattern for non-retried forum and membership mutation helpers.
- This slice intentionally targets only `PrivateMessage.send(...)`; site member permission changes and site application accept/decline actions remain separate action boundaries.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, raw action responses, private message bodies, private message subjects, page source text, page names from real sites, and site contents out of upstream discussion.

## Additional Notes

This slice intentionally does not retry private-message sends, change request construction, add per-send result objects, change inbox/sentbox acquisition, touch message detail parsing, touch site member permission mutation helpers, touch site application accept/decline helpers, or modify live Wikidot behavior. It only validates the returned dashboard message send action response before accepting `PrivateMessage.send(...)` as successful.
