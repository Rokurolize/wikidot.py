# PR Draft: Validate Private Message Data-Href ID Shape

## Summary

`PrivateMessageInbox.acquire(...)` and `PrivateMessageSentBox.acquire(...)` parse dashboard message-list rows and pass collected IDs to `PrivateMessageCollection.from_ids(...)` for detail fetching. Earlier private-message list work added retry handling, module/page/row diagnostics, first-page reuse, nested-row filtering, deduplication, and missing/no-ID `data-href` errors, but the ID extraction still accepted any trailing digit run. A malformed generated `data-href` such as `/account/messages/view/message-123` was therefore accepted as message ID `123`.

This change treats a private-message list ID as valid only when it appears as the terminal numeric URL-like path segment, with optional trailing slash, query, or fragment text. Digit-bearing malformed `data-href` values now raise `NoElementException` with module, page, row, and raw `data-href` context before any detail fetch is attempted.

## Outcome

Private-message list acquisition no longer fabricates message IDs from digits embedded in non-ID path segments. Valid list routes such as `/account/messages/view/123` still parse the same message IDs, and routes without any digits keep the existing `Message ID is not found ...` diagnostic.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators using browser-free inbox/sent-box reads, private-message ledgers, moderation notifications, migration checks, generated fixtures, local read-model tests, or `Client.private_message` accessors where message identity must come from structurally valid dashboard list rows.

## Current Evidence

Local rollout-backed drafts repeatedly identify private-message list/detail acquisition as a practical read-heavy workflow. Existing drafts cover retry-aware private-message fetching, duplicate detail-fetch deduplication, direct empty fetch fast paths, first-page body reuse, module/page/row list diagnostics, list fetch failure context, nested message-row filtering, message-row pager filtering, detail response-body diagnostics, private-message detail user/timestamp/subject/body parser context, direct message-ID input validation, direct `PrivateMessage.id` validation, retained message-ID validation in collections, participant identity validation, and send action validation.

This slice is not a duplicate of [037-pr-retry-private-message-fetches.md](037-pr-retry-private-message-fetches.md), [054-pr-deduplicate-private-message-detail-fetches.md](054-pr-deduplicate-private-message-detail-fetches.md), [067-pr-deduplicate-direct-private-message-fetches.md](067-pr-deduplicate-direct-private-message-fetches.md), [077-pr-skip-empty-private-message-fetch-batches.md](077-pr-skip-empty-private-message-fetch-batches.md), [133-pr-reuse-private-message-list-first-page-body.md](133-pr-reuse-private-message-list-first-page-body.md), [163-pr-private-message-list-row-error-context.md](163-pr-private-message-list-row-error-context.md), [178-pr-private-message-list-fetch-failure-context.md](178-pr-private-message-list-fetch-failure-context.md), [288-pr-private-message-detail-user-context.md](288-pr-private-message-detail-user-context.md), [321-pr-private-message-response-body-type-context.md](321-pr-private-message-response-body-type-context.md), [361-pr-validate-private-message-message-id-inputs.md](361-pr-validate-private-message-message-id-inputs.md), [425-pr-validate-private-message-collection-initialization.md](425-pr-validate-private-message-collection-initialization.md), [692-pr-validate-private-message-constructor-user-id-state.md](692-pr-validate-private-message-constructor-user-id-state.md), or [715-pr-validate-private-message-send-status-type.md](715-pr-validate-private-message-send-status-type.md). Those drafts cover request reliability, duplicate work, empty/direct inputs, missing row fields, list/detail diagnostics, response-body typing, direct ID APIs, collection construction, participant state, and send status handling. This slice covers generated list-row `data-href` ID-shape validation before private-message detail IDs are fetched.

No upstream issue was filed from this local workspace.

## Changes

- Add a focused helper for private-message list `data-href` ID parsing.
- Accept message IDs only from a terminal numeric URL-like path segment, preserving valid `/account/messages/view/123` rows.
- Reject digit-bearing malformed list `data-href` values, such as `/account/messages/view/message-123`, with `NoElementException` containing module, page, row, and raw `data-href` context.
- Preserve the existing missing-ID `Message ID is not found ...` diagnostic for list rows without digits.
- Preserve private-message list pagination, retry behavior, first-page body reuse, nested-row filtering, pager filtering, ordered deduplication, detail fetch delegation, inbox/sent wrappers, direct message lookup, detail parsing, and send behavior.

## Type Of Change

- Parser hardening
- Private-message identity validation
- Regression test

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | A generated private-message list `data-href` containing digits embedded in a non-ID path segment, such as `/account/messages/view/message-123`, must fail before `PrivateMessageCollection.from_ids(...)` is called. |
| R2 | The malformed message-ID error must identify the dashboard module, list page, structural row, and raw `data-href` value. |
| R3 | Valid generated list `data-href` values ending in a numeric path segment must continue to parse into the same message IDs. |
| R4 | `data-href` values without any digits must keep the existing `Message ID is not found ...` diagnostic. |
| R5 | Existing list pagination, retry handling, response-body diagnostics, pager filtering, nested-row filtering, ordered deduplication, detail fetch delegation, inbox/sent wrappers, direct message lookup, detail parsing, and send behavior must remain unchanged. |
| R6 | The draft and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private message subjects/bodies, raw private list HTML, pushes, upstream Issues, or upstream PRs. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | `/account/messages/view/message-123` fails instead of becoming message ID `123`. | `test_acquire_rejects_message_href_with_embedded_id_segment` failed RED with `DID NOT RAISE`, then passed GREEN after strict terminal numeric-segment parsing was added. | Returning a detail collection, calling `from_ids(...)`, extracting the trailing digit run, or silently dropping segment text rejects this local completion claim. | Private-message list generated parser | `src/wikidot/module/private_message.py`, `tests/unit/test_private_message.py` |
| R2 | The malformed `data-href` diagnostic includes module, page, row, and observed value. | The regression matches `Message ID is malformed in data-href: /account/messages/view/message-123 for module: dashboard/messages/DMInboxModule (page=1, row=1)`. | Omitting module, page, row, or raw `data-href` value rejects this local completion claim. | Private-message list ID diagnostics | `tests/unit/test_private_message.py` |
| R3 | Valid message-list routes still parse. | Focused GREEN included valid `/account/messages/view/123` acquisition tests; `tests/unit/test_private_message.py` passed 169 tests. | Rejecting valid list routes or changing parsed message IDs rejects this local completion claim. | Successful private-message list acquisition | `tests/unit/test_private_message.py` |
| R4 | Existing no-digit behavior remains distinct from malformed digit-bearing routes. | `test_acquire_malformed_message_href_raises` passed with the existing `Message ID is not found ...` diagnostic. | Reclassifying no-digit links as malformed digit-bearing links or dropping existing parse context rejects this local completion claim. | Existing parser diagnostic compatibility | `tests/unit/test_private_message.py` |
| R5 | Adjacent repository behavior stays green. | Adjacent private-message/client/user/parser coverage, full unit, ruff, ruff format, mypy, pyright, and `git diff --check` passed. | Any test, lint, format, type, or whitespace failure rejects this local completion claim. | Repository quality gates | `tests/unit`, `src`, `tests` |
| R6 | No private or live-site material is needed. | The regression mutates a synthetic unit fixture and uses mocks only. | Using credentials, cookies, auth JSON, live Wikidot actions, raw private generated HTML, private message subjects/bodies, upstream Issues, upstream PRs, or pushes rejects this local completion claim. | Test and draft privacy | this draft |

## Testing

Implemented locally in commit `e775d06 fix(private_message): validate list data href ids`.

- RED: `uv run pytest tests/unit/test_private_message.py::TestPrivateMessageCollection::test_acquire_rejects_message_href_with_embedded_id_segment -q` failed before the fix with `DID NOT RAISE`.
- GREEN focused: `uv run pytest tests/unit/test_private_message.py::TestPrivateMessageCollection::test_acquire_malformed_message_href_raises tests/unit/test_private_message.py::TestPrivateMessageCollection::test_acquire_rejects_message_href_with_embedded_id_segment tests/unit/test_private_message.py::TestPrivateMessageCollection::test_acquire_ignores_non_numeric_pager_targets tests/unit/test_private_message.py::TestPrivateMessageCollection::test_acquire_reuses_first_page_body_for_message_ids tests/unit/test_private_message.py::TestPrivateMessageCollection::test_acquire_deduplicates_message_ids_preserving_order -q` passed 5 tests.
- `uv run pytest tests/unit/test_private_message.py -q` passed 169 tests.
- `uv run pytest tests/unit/test_private_message.py tests/unit/test_client.py tests/unit/test_user.py tests/unit/parsers/test_user_parser.py -q` passed 350 tests.
- `uv run pytest tests/unit -q` passed 3601 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted after applying `uv run ruff format src/wikidot/module/private_message.py`.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `PrivateMessageCollection._acquire(...)` raises `NoElementException` for a list-row `data-href` such as `/account/messages/view/message-123`.
- The exception includes the requested dashboard module, list page number, structural row number, and raw `data-href` value.
- Valid list-row `data-href` values ending with a numeric path segment still parse the same message IDs.
- `data-href` values with no digits keep the existing `Message ID is not found ...` parser diagnostic.
- Successful inbox/sent-box acquisition, pagination, retry behavior, first-page body reuse, empty-result behavior, response-body validation, nested-row filtering, pager filtering, duplicate ID deduplication, detail fetch delegation, direct message lookup, detail parser behavior, client accessors, and send behavior remain unchanged.
- No live Wikidot action, credential, cookie, auth JSON, upstream Issue, upstream PR, or push is required for this local draft.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread HTML report and complexity memo are refreshed after the docs commit.
- Secret and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: Private-message routes may include query strings or fragments. Mitigation: the helper accepts a terminal numeric segment followed by optional trailing slash, query, or fragment text.
- Risk: Overly loose parsing could continue accepting non-ID segments. Mitigation: the helper rejects any digit-bearing value that lacks a terminal numeric path segment.
- Risk: This could be confused with public direct message-ID validation. Mitigation: Issues 361 and the direct constructor/collection validation drafts cover caller-provided IDs and retained local state; this slice validates generated dashboard list `data-href` input before detail fetching.

## Dependencies

- Existing `PrivateMessageCollection._acquire(...)` request construction, retry helper usage, response-body validation, pager parsing, row selection, deduplication, and detail delegation remain unchanged.
- Existing `PrivateMessageCollection.from_ids(...)` and `PrivateMessage` constructor validation remain responsible for direct caller input and local record construction.
- Existing `NoElementException` remains the generated-parser exception for malformed private-message list fields.
- No new dependency, live Wikidot action, credential, or upstream API change is required.

## Open Questions

None for this local slice. Future work should continue with fresh duplicate-checked parser boundaries, response-shape validation, direct input validation, result ergonomics, or measured complexity candidates outside this private-message list `data-href` ID-shape path.

## Upstream-Safe Motivation

Private-message IDs are durable identity metadata for browser-free inbox/sent-box reads, audit ledgers, moderation workflows, migration checks, and local fixtures. A generated list-row `data-href` with digits embedded in a non-ID segment should not be accepted merely because it ends with a digit run. Terminal segment validation keeps malformed dashboard output visible while preserving valid private-message rows.

## Local Evidence, Not For Upstream Paste

- Local rollout-backed work established private-message list/detail acquisition as a practical workflow through retry-aware fetching, parser scoping, response-body validation, row diagnostics, duplicate handling, direct input validation, detail parser diagnostics, and send action validation.
- Existing local drafts covered missing list-row field diagnostics, no-ID `data-href` diagnostics, direct message-ID input validation, duplicate list/detail behavior, response-body typing, and private-message detail parsing; they did not reject digit-bearing non-ID `data-href` segments before detail fetching.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, cookies, auth JSON, raw private-message list HTML, message subjects, message bodies, usernames, and live account details out of upstream discussion.
