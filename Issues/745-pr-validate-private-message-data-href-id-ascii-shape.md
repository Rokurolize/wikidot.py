# PR Draft: Validate Private Message Data-Href ID ASCII Shape

## Summary

`PrivateMessageInbox.acquire(...)` and `PrivateMessageSentBox.acquire(...)` parse generated dashboard message-list row `data-href` values into message IDs before delegating detail fetches to `PrivateMessageCollection.from_ids(...)`. Issues [728-pr-validate-private-message-data-href-id-shape.md](728-pr-validate-private-message-data-href-id-shape.md) and [742-pr-validate-private-message-data-href-routes.md](742-pr-validate-private-message-data-href-routes.md) made embedded non-ID segments and invalid routes fail, but the terminal ID segment still used Python regex `\d+`. That allowed Unicode decimal digit glyphs such as `/account/messages/view/\uff11\uff12\uff13` to normalize into ordinary message ID `123`.

This change requires the private-message list route ID segment to match ASCII digits before integer conversion. Valid generated routes such as `/account/messages/view/123` and absolute `https://www.wikidot.com/account/messages/view/123?from=list#row` remain compatible, while present non-ASCII digit payloads now raise the existing contextual malformed-`data-href` `NoElementException`.

## Outcome

Browser-free inbox/sent-box acquisition no longer fabricates private-message identities by normalizing non-ASCII digit glyphs from generated dashboard route metadata. The malformed-value diagnostic remains actionable and does not include raw private-message HTML, subjects, or bodies.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators using browser-free private-message inbox/sent-box reads, notification ledgers, moderation workflows, migration checks, generated fixtures, local read-model tests, `Client.private_message`, `PrivateMessageInbox`, or `PrivateMessageSentBox` where message identity must come from structurally valid dashboard list rows.

## Current Evidence

Local rollout-backed drafts repeatedly identify private-message list/detail acquisition as a practical read-heavy workflow. Existing drafts cover retry-aware private-message fetching, duplicate detail-fetch deduplication, empty direct fetch fast paths, first-page body reuse, module/page/row list diagnostics, list fetch failure context, nested message-row filtering, message-row pager filtering, detail response-body diagnostics, detail parser context, direct message-ID input validation, retained message-ID validation, participant identity validation, send action validation, generated list `data-href` ID-segment shape validation, and generated list `data-href` route validation.

This slice is not a duplicate of [728-pr-validate-private-message-data-href-id-shape.md](728-pr-validate-private-message-data-href-id-shape.md) or [742-pr-validate-private-message-data-href-routes.md](742-pr-validate-private-message-data-href-routes.md). Issue 728 covers embedded non-ID segment text such as `message-123`; Issue 742 covers route, scheme, and host shape before accepting a numeric segment. This slice covers Unicode digit normalization in an otherwise valid dashboard message-view ID segment.

No upstream issue was filed from this local workspace.

## Related Issues

Builds on [728-pr-validate-private-message-data-href-id-shape.md](728-pr-validate-private-message-data-href-id-shape.md), [742-pr-validate-private-message-data-href-routes.md](742-pr-validate-private-message-data-href-routes.md), [361-pr-validate-private-message-message-id-inputs.md](361-pr-validate-private-message-message-id-inputs.md), [425-pr-validate-private-message-collection-initialization.md](425-pr-validate-private-message-collection-initialization.md), [674-pr-validate-private-message-collection-retained-id-state.md](674-pr-validate-private-message-collection-retained-id-state.md), [692-pr-validate-private-message-constructor-user-id-state.md](692-pr-validate-private-message-constructor-user-id-state.md), [715-pr-validate-private-message-send-status-type.md](715-pr-validate-private-message-send-status-type.md), and [743-pr-validate-forum-thread-script-id-ascii-shape.md](743-pr-validate-forum-thread-script-id-ascii-shape.md).

## Changes

- Require private-message list `account/messages/view/<id>` path IDs to match `[0-9]+` before `int(...)`.
- Preserve valid relative dashboard message-view routes and absolute `www.wikidot.com` HTTP(S) message-view routes.
- Preserve existing no-digit `Message ID is not found ...` diagnostics, embedded-ID malformed diagnostics, route/scheme/host malformed diagnostics, pagination, retry behavior, first-page body reuse, nested-row filtering, pager filtering, ordered deduplication, detail fetch delegation, inbox/sent wrappers, direct message lookup, detail parsing, and send behavior.
- Add focused regression coverage for escaped fullwidth message ID text `\uff11\uff12\uff13`.

## Type Of Change

- Bug fix
- Private-message parser scalar-shape validation
- Regression test

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | A generated private-message list `data-href` with a non-ASCII digit ID segment must fail before `PrivateMessageCollection.from_ids(...)` is called. |
| R2 | The malformed `data-href` error must preserve existing module, page, row, and observed value context. |
| R3 | Valid relative and absolute `www.wikidot.com` ASCII message-view routes must continue to parse the same message IDs. |
| R4 | Existing no-digit, embedded non-ID segment, and route/scheme/host diagnostics must remain compatible. |
| R5 | Existing private-message list/detail workflows and adjacent client/user/parser workflows must remain compatible. |
| R6 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private message subjects/bodies, raw private list HTML, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R7 | Focused RED/GREEN, private-message tests, adjacent private-message/client/user/parser tests, full unit tests, lint, format, type, pyright, and whitespace gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | `/account/messages/view/\uff11\uff12\uff13` raises before detail-fetch delegation. | `test_acquire_rejects_non_ascii_digit_message_href_id` failed RED with `DID NOT RAISE`, then passed after ASCII-only ID validation. | Calling `from_ids(...)`, storing message ID `123`, or silently dropping the row rejects this local completion claim. | Private-message list parser | `src/wikidot/module/private_message.py`, `tests/unit/test_private_message.py` |
| R2 | The malformed diagnostic includes module, page, row, and raw `data-href` value. | The focused regression matches the existing malformed-route message family. | Omitting structural context or the observed value rejects this local completion claim. | Parser diagnostics | focused test |
| R3 | Valid generated ASCII routes continue to work. | Focused GREEN included `test_acquire_preserves_wikidot_absolute_message_href` and first-page body reuse over `/account/messages/view/123`. | Rejecting valid relative or `www.wikidot.com` dashboard links rejects this local completion claim. | Valid data-href compatibility | private-message tests |
| R4 | Existing malformed branches stay green. | Focused GREEN included embedded-ID and malformed-route regressions. | Reclassifying no-ID links, embedded-ID links, or invalid routes into a different diagnostic family rejects this local completion claim. | Prior parser branches | private-message tests |
| R5 | Adjacent workflows remain green. | `tests/unit/test_private_message.py` passed 178 tests, adjacent private-message/client/user/parser coverage passed 367 tests, and full unit passed 3746 tests. | Regressing list pagination, retry, response-body diagnostics, nested-row/pager filtering, deduplication, detail fetching, wrappers, direct lookup, detail parsing, send behavior, client accessors, user parsing, or any unit test rejects this local completion claim. | Private-message workflows | `tests/unit` |
| R6 | No live site state or private material is needed. | The regression uses synthetic unit-level dashboard list HTML and mocked responses. | Using credentials, cookies, auth JSON, raw private payloads, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, private message subjects, private message bodies, real usernames, or account data rejects this local completion claim. | Test and draft privacy | this draft |
| R7 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN, private-message tests, adjacent tests, full unit, ruff, format, mypy, pyright, and whitespace checks passed. | Test, lint, format, type, pyright, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `f0f91f9 fix(private_message): validate data href id ascii shape`.

- RED: `uv run --extra test pytest tests/unit/test_private_message.py::TestPrivateMessageCollection::test_acquire_rejects_non_ascii_digit_message_href_id -q` failed before the fix with `DID NOT RAISE` because `/account/messages/view/\uff11\uff12\uff13` was accepted and normalized as message ID `123`.
- GREEN focused: `uv run --extra test pytest tests/unit/test_private_message.py::TestPrivateMessageCollection::test_acquire_rejects_non_ascii_digit_message_href_id tests/unit/test_private_message.py::TestPrivateMessageCollection::test_acquire_rejects_message_href_with_embedded_id_segment tests/unit/test_private_message.py::TestPrivateMessageCollection::test_acquire_rejects_malformed_message_href_routes tests/unit/test_private_message.py::TestPrivateMessageCollection::test_acquire_preserves_wikidot_absolute_message_href tests/unit/test_private_message.py::TestPrivateMessageCollection::test_acquire_reuses_first_page_body_for_message_ids -q` passed 11 tests.
- `uv run --extra test pytest tests/unit/test_private_message.py -q` passed 178 tests.
- `uv run --extra test pytest tests/unit/test_private_message.py tests/unit/test_client.py tests/unit/test_user.py tests/unit/parsers/test_user_parser.py -q` passed 367 tests.
- `uv run --extra test pytest tests/unit -q` passed 3746 tests.
- `uv run --extra lint ruff check src tests` passed.
- `uv run --extra format ruff format --check src tests` passed with 87 files already formatted.
- `uv run --extra lint mypy src tests --install-types --non-interactive` passed with no issues in 87 source files, plus existing annotation notes.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `PrivateMessageCollection._acquire(...)` raises contextual `NoElementException` for a present generated `data-href` built from escaped fullwidth digit text `/account/messages/view/\uff11\uff12\uff13`.
- The exception includes dashboard module, list page number, structural row number, and raw `data-href` value.
- Valid relative dashboard message links such as `/account/messages/view/123` still parse message ID `123`.
- Valid absolute dashboard message links such as `https://www.wikidot.com/account/messages/view/123?from=list#row` still parse message ID `123`.
- Existing no-digit behavior, embedded non-ID segment behavior, and malformed route/scheme/host behavior remain on their existing diagnostic paths.
- Existing pagination, retry handling, first-page body reuse, response-body validation, nested-row filtering, pager filtering, duplicate ID deduplication, detail fetch delegation, inbox/sent wrappers, direct message lookup, detail parser behavior, client accessors, and send behavior remain unchanged.
- No live Wikidot action, credential, cookie, auth JSON, upstream Issue, upstream PR, push, raw real private-message list HTML, raw rollout path, private message subject/body, real username, or account data is required for this local draft.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread HTML report and complexity memo are refreshed after the docs commit.
- Secret and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: This could be confused with Issues 728 or 742. Mitigation: those issues cover embedded non-ID segment text and route/scheme/host shape; this slice covers Unicode digit normalization that still passes those branches.
- Risk: Tightening private-message ID parsing could reject unusual but valid generated dashboard output. Mitigation: Wikidot dashboard message IDs in fixtures are ordinary ASCII decimal digits, and valid relative plus `www.wikidot.com` dashboard routes remain tested.
- Risk: Diagnostics could expose private payloads. Mitigation: the diagnostic reports only the scalar `data-href` value plus module/page/row context, not response bodies, credentials, cookies, message subjects, message bodies, local paths, or account data.

## Dependencies

- Dashboard private-message list modules continue to represent message detail links as relative `/account/messages/view/<id>` routes or `www.wikidot.com` HTTP(S) routes.
- `PrivateMessageCollection._acquire(...)` remains the internal list parser used by `PrivateMessageInbox.acquire(...)` and `PrivateMessageSentBox.acquire(...)`.
- `PrivateMessage.id` direct constructor and direct lookup validation remain unchanged.

## Open Questions

None for this local slice. Future private-message parser changes should be selected only after a fresh duplicate check and public RED test.

## Upstream-Safe Motivation

Private-message IDs are durable identity metadata for browser-free inbox/sent-box reads, notification ledgers, moderation workflows, migration checks, generated fixtures, and client accessors. Unicode digit normalization can silently turn malformed generated dashboard route metadata into a valid-looking message ID. Requiring ASCII digits keeps generated identity parsing strict and consistent with adjacent page-file and forum-thread scalar-shape fixes while preserving valid dashboard links.

## Local Evidence, Not For Upstream Paste

- The focused RED test demonstrated prior behavior: escaped fullwidth digit route IDs were accepted and normalized to message ID `123`.
- Existing local drafts covered retry behavior, duplicate detail fetching, direct empty/direct ID behavior, first-page reuse, row diagnostics, response-body typing, missing/no-ID `data-href` diagnostics, embedded non-ID segment diagnostics, route/scheme/host diagnostics, detail parser diagnostics, constructor fields, retained message ID state, and send action validation; they did not validate Unicode digit normalization in generated private-message `data-href` ID scalars.
- This slice does not change request payloads, retry policy, message row selectors, list pagination, first-page response reuse, nested-row/pager filtering, duplicate ID handling, detail fetch response parsing, direct `PrivateMessage` constructor rules, inbox/sent wrapper behavior, live Wikidot behavior, upstream filing state, or valid relative/`www.wikidot.com` HTTP(S) dashboard output.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, cookies, auth JSON, generated private-message list HTML from real accounts, private message subjects, private message bodies, real usernames, and live account data out of upstream discussion.
