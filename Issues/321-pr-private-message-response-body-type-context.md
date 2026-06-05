# PR Draft: Report Malformed Private Message Response Body Types

## Summary

`PrivateMessageCollection.from_ids(...)`, `PrivateMessageInbox.acquire(...)`, and `PrivateMessageSentBox.acquire(...)` parse Wikidot dashboard AMC response `body` fields as generated HTML. Earlier local slices made private-message reads retry-aware, deduplicated detail fetches, reused parsed details, preserved message text spacing, scoped detail/list parser boundaries, and converted missing detail/list `body` fields into contextual `NoElementException` failures. One adjacent response-boundary gap remained: if the decoded AMC response was a dictionary with a present but non-string `body` value, the code passed that value into BeautifulSoup and leaked low-level parser exceptions such as `AttributeError` or `TypeError`.

This local slice validates present private-message response `body` values before HTML parsing. Non-string detail bodies now raise module/message-specific `NoElementException`, and non-string list bodies now raise module/page-specific `NoElementException`. The diagnostics report only compact structural context, `field=body`, expected type, and observed type; they do not include raw private-message HTML, previews, message bodies, or response JSON.

## Outcome

Malformed private-message response body types now fail at the module response boundary with actionable module/message or module/page context instead of BeautifulSoup internals.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use private-message inbox, sent-box, or direct message reads in browser-free moderation, archival, triage, or migration tooling.

## Related Issue

Builds on [037-pr-retry-private-message-fetches.md](037-pr-retry-private-message-fetches.md), [073-pr-reuse-private-message-detail-parsing.md](073-pr-reuse-private-message-detail-parsing.md), [101-pr-ignore-private-message-row-pager-markup.md](101-pr-ignore-private-message-row-pager-markup.md), [102-pr-ignore-private-message-nested-row-markup.md](102-pr-ignore-private-message-nested-row-markup.md), [106-pr-preserve-private-message-body-spacing.md](106-pr-preserve-private-message-body-spacing.md), [119-pr-preserve-private-message-subject-spacing.md](119-pr-preserve-private-message-subject-spacing.md), [163-pr-private-message-list-row-error-context.md](163-pr-private-message-list-row-error-context.md), [178-pr-private-message-list-fetch-failure-context.md](178-pr-private-message-list-fetch-failure-context.md), [184-pr-private-message-detail-fetch-context.md](184-pr-private-message-detail-fetch-context.md), [188-pr-private-message-detail-parse-context.md](188-pr-private-message-detail-parse-context.md), [206-pr-private-message-detail-response-body-context.md](206-pr-private-message-detail-response-body-context.md), [207-pr-private-message-list-response-body-context.md](207-pr-private-message-list-response-body-context.md), [287-pr-private-message-detail-timestamp-value-context.md](287-pr-private-message-detail-timestamp-value-context.md), and [288-pr-private-message-detail-user-context.md](288-pr-private-message-detail-user-context.md). Those drafts established private-message reads as practical, retry-aware, parser-scoped, privacy-sensitive workflows while leaving present non-string response bodies as a separate parser-entry boundary.

No upstream issue was filed from this local workspace.

## Changes

- Validate direct private-message detail response `body` values are strings before BeautifulSoup parsing.
- Validate private-message list response `body` values are strings before pager or row parsing.
- Convert malformed present detail body values into module/message-specific `NoElementException`.
- Convert malformed present list body values into module/page-specific `NoElementException`.
- Preserve missing-body diagnostics, retry-exhausted behavior, `no_message` handling, duplicate-ID behavior, duplicate parsed-detail reuse, row parser context, inbox/sent wrappers, sender/recipient parsing, subject/body spacing, date parsing, and send behavior.

## Type Of Change

- Bug fix / diagnostics improvement
- Private-message response-body type validation
- Test update

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | A direct private-message detail response with a present non-string `body` field must fail before BeautifulSoup parsing. |
| R2 | A private-message list response with a present non-string `body` field must fail before pager, row, or detail-fetch work. |
| R3 | Malformed-body-type errors must identify module/message or module/page, `field=body`, expected type, and observed type while omitting raw private-message content. |
| R4 | Existing private-message behavior, Issues 206/207 missing-body diagnostics, adjacent client behavior, and repository quality gates must remain compatible. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | `PrivateMessageCollection.from_ids(...)` raises contextual `NoElementException` when `dashboard/messages/DMViewMessageModule` returns a list-valued `body`. | `TestPrivateMessageCollection.test_from_ids_malformed_detail_response_body_type_includes_module_message_and_type_context` expects `Message response body is malformed for module: dashboard/messages/DMViewMessageModule, message: 1 (field=body, expected=str, actual=list)`. | Leaking BeautifulSoup `AttributeError`, parsing user/date fields, constructing a message, or including raw private-message content rejects this local completion claim. | Private-message detail reads | `tests/unit/test_private_message.py` |
| R2 | `PrivateMessageInbox.acquire(...)` raises contextual `NoElementException` when the first list page returns an integer-valued `body`. | `TestPrivateMessageCollection.test_acquire_malformed_first_page_response_body_type_includes_module_page_and_type_context` expects `Message list response body is malformed for module: dashboard/messages/DMInboxModule, page: 1 (field=body, expected=str, actual=int)`. | Leaking BeautifulSoup `TypeError`, calling `from_ids(...)`, returning an empty or partial list, or hiding module/page context rejects this local completion claim. | Private-message inbox/sent list reads | `tests/unit/test_private_message.py` |
| R3 | Detail/list malformed-body-type diagnostics include only structural context and type names. | The focused regressions match full message shapes and use synthetic list/int body values. | Including raw response JSON, raw HTML, message previews, message bodies, credentials, local rollout paths, or account names rejects this local completion claim. | Private-message diagnostics | `src/wikidot/module/private_message.py` |
| R4 | Existing private-message and adjacent client behavior remains green. | The private-message suite passed 45 tests, the client/private-message run passed 64 tests, and the full unit suite passed 888 tests. | Regressing missing-body diagnostics, retry behavior, `no_message`, duplicate-ID handling, duplicate parsed-detail reuse, row filtering, sender/recipient parsing, timestamp/user diagnostics, subject/body spacing, inbox/sent wrappers, send behavior, or client accessors rejects this local completion claim. | Client/private-message workflows | `tests/unit/test_client.py`; `tests/unit/test_private_message.py` |

## Testing

Implemented locally in commit `31edf9a fix(private_message): report malformed body types`.

- RED: `uv run --extra test pytest tests/unit/test_private_message.py::TestPrivateMessageCollection::test_from_ids_malformed_detail_response_body_type_includes_module_message_and_type_context tests/unit/test_private_message.py::TestPrivateMessageCollection::test_acquire_malformed_first_page_response_body_type_includes_module_page_and_type_context -q` failed before the fix with BeautifulSoup `AttributeError` for the list-valued detail body and `TypeError` for the integer-valued list body.
- GREEN: `uv run --extra test pytest tests/unit/test_private_message.py::TestPrivateMessageCollection::test_from_ids_malformed_detail_response_body_type_includes_module_message_and_type_context tests/unit/test_private_message.py::TestPrivateMessageCollection::test_acquire_malformed_first_page_response_body_type_includes_module_page_and_type_context -q` passed 2 tests.
- `uv run --extra test pytest tests/unit/test_private_message.py -q` passed 45 tests.
- `uv run --extra test pytest tests/unit/test_client.py tests/unit/test_private_message.py -q` passed 64 tests.
- `uv run --extra test pytest tests/unit -q` passed 888 tests.
- `uv run ruff check` passed.
- `uv run ruff format --check` passed with 80 files already formatted.
- `uv run mypy . --install-types --non-interactive` passed with no issues in 80 source files.
- `git diff --check` passed.

Not run successfully: `uv run pyright` failed because `pyright` was not installed in this environment.

## Acceptance Criteria

- Direct private-message detail reads still request `dashboard/messages/DMViewMessageModule` with the same item payloads.
- Inbox and sent-box list reads still request their existing dashboard modules and still use the same pagination flow.
- Missing `body` fields still raise the existing not-found diagnostics from Issues 206 and 207.
- Present non-string detail `body` values raise contextual `NoElementException` before BeautifulSoup parsing.
- Present non-string list `body` values raise contextual `NoElementException` before pager, row, or detail-fetch work.
- The malformed-body-type messages include module, message or page, `field=body`, expected type, and observed type.
- The malformed-body-type messages do not include raw response JSON, raw private-message HTML, previews, message bodies, credentials, local rollout paths, or private account material.
- Existing retry-exhausted behavior, `no_message` handling, duplicate-ID behavior, duplicate parsed-detail reuse, row-local pager filtering, nested-row filtering, sender/recipient parsing, timestamp/user diagnostics, subject/body spacing, inbox/sent wrappers, and send behavior remain unchanged.
- No live Wikidot action, upstream Issue, upstream PR, push, real private-message response body, local rollout path, account material, or message content is required for this local draft.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread HTML report and complexity memo are refreshed after the docs commit.
- Private-data and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: Type validation could treat a future bytes-like body as malformed. Mitigation: AMC JSON bodies are expected to decode generated HTML as strings; preserving only string input keeps the parser boundary explicit.
- Risk: Type validation could mask missing-body diagnostics. Mitigation: `None` remains on the existing missing-body path; only present non-string values use the malformed-type diagnostic.
- Risk: Diagnostics could expose private-message content. Mitigation: messages include module/page or module/message and type names only.

## Dependencies

- The AMC connector already validates decoded response roots as dictionaries before normal module parsing; this slice targets the `body` field value within that dictionary.
- Private-message detail/list HTML parser behavior remains unchanged after a valid string body is supplied.

## Open Questions

None for this local slice. Remaining useful work should continue the broader response-body field-type audit across other modules rather than expanding this private-message change beyond its detail/list boundaries.

## Upstream-Safe Motivation

Private-message reads are useful for browser-free inbox and sent-box tooling, but logs for these workflows often cannot retain raw message HTML or bodies. If a generated dashboard response contains a present non-string `body`, wikidot.py should report the affected module/page or module/message and type mismatch before BeautifulSoup internals obscure the failure.

## Local Evidence, Not For Upstream Paste

- The RED failures showed a list-valued detail `body` leaking BeautifulSoup `AttributeError` and an integer-valued list `body` leaking BeautifulSoup `TypeError`.
- Existing Issues 206 and 207 covered missing `body` fields but intentionally left present malformed values as a separate boundary.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, raw response JSON, raw private-message HTML, message previews, and message bodies out of upstream discussion.

## Additional Notes

This is a response-body field type diagnostics fix. It preserves valid private-message behavior while making malformed present response bodies actionable without retaining private message content.
