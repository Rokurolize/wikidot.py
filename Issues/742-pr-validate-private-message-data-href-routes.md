# PR Draft: Validate Private Message Data-Href Routes

## Summary

`PrivateMessageInbox.acquire(...)` and `PrivateMessageSentBox.acquire(...)` parse generated dashboard message-list row `data-href` values into message IDs before delegating detail fetches to `PrivateMessageCollection.from_ids(...)`. Issue [728-pr-validate-private-message-data-href-id-shape.md](728-pr-validate-private-message-data-href-id-shape.md) made digit-bearing non-ID segments such as `/account/messages/view/message-123` fail instead of becoming message ID `123`, but the parser still accepted any route whose parsed text ended in a numeric segment. As a result, `http://example.com/account/messages/view/123`, `https://other-site.wikidot.com/account/messages/view/123`, `http:account/messages/view/123`, `javascript:/account/messages/view/123`, `mailto:account/messages/view/123`, `/account/messages/read/123`, and `/other/messages/view/123` could become private message ID `123`.

This change validates private-message list `data-href` route shape before extracting the message ID. Relative dashboard message-view routes and absolute `www.wikidot.com` HTTP(S) dashboard routes remain compatible, while foreign-host, hostless-HTTP, non-HTTP(S), and non-message-view present routes raise contextual `NoElementException`.

## Outcome

Browser-free inbox/sent-box acquisition no longer fabricates private-message identities from foreign absolute URLs, other-site Wikidot URLs, hostless HTTP strings, JavaScript URLs, mailto URLs, or unrelated dashboard/account routes. Valid routes such as `/account/messages/view/123` and `https://www.wikidot.com/account/messages/view/123?from=list#row` continue to parse the same message IDs.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators using browser-free private-message inbox/sent-box reads, notification ledgers, moderation workflows, migration checks, generated fixtures, local read-model tests, `Client.private_message`, `PrivateMessageInbox`, or `PrivateMessageSentBox` where message identity must come from structurally valid dashboard list rows.

## Current Evidence

Local rollout-backed drafts repeatedly identify private-message list/detail acquisition as a practical read-heavy workflow. Existing drafts cover retry-aware private-message fetching, duplicate detail-fetch deduplication, empty direct fetch fast paths, first-page body reuse, module/page/row list diagnostics, list fetch failure context, nested message-row filtering, message-row pager filtering, detail response-body diagnostics, private-message detail user/timestamp/subject/body parser context, direct message-ID input validation, direct `PrivateMessage.id` validation, retained message-ID validation in collections, participant identity validation, private-message send action validation, and generated list `data-href` ID-segment shape validation.

This slice is not a duplicate of [037-pr-retry-private-message-fetches.md](037-pr-retry-private-message-fetches.md), [054-pr-deduplicate-private-message-detail-fetches.md](054-pr-deduplicate-private-message-detail-fetches.md), [067-pr-deduplicate-direct-private-message-fetches.md](067-pr-deduplicate-direct-private-message-fetches.md), [077-pr-skip-empty-private-message-fetch-batches.md](077-pr-skip-empty-private-message-fetch-batches.md), [133-pr-reuse-private-message-list-first-page-body.md](133-pr-reuse-private-message-list-first-page-body.md), [163-pr-private-message-list-row-error-context.md](163-pr-private-message-list-row-error-context.md), [178-pr-private-message-list-fetch-failure-context.md](178-pr-private-message-list-fetch-failure-context.md), [288-pr-private-message-detail-user-context.md](288-pr-private-message-detail-user-context.md), [321-pr-private-message-response-body-type-context.md](321-pr-private-message-response-body-type-context.md), [361-pr-validate-private-message-message-id-inputs.md](361-pr-validate-private-message-message-id-inputs.md), [425-pr-validate-private-message-collection-initialization.md](425-pr-validate-private-message-collection-initialization.md), [692-pr-validate-private-message-constructor-user-id-state.md](692-pr-validate-private-message-constructor-user-id-state.md), [715-pr-validate-private-message-send-status-type.md](715-pr-validate-private-message-send-status-type.md), or [728-pr-validate-private-message-data-href-id-shape.md](728-pr-validate-private-message-data-href-id-shape.md). Issue 728 covers terminal numeric ID segment shape once the generated `data-href` is otherwise treated as a private-message route. This slice covers route, scheme, and host validation before any numeric segment is accepted as a dashboard private-message identity.

No upstream issue was filed from this local workspace.

## Related Issues

Builds on [728-pr-validate-private-message-data-href-id-shape.md](728-pr-validate-private-message-data-href-id-shape.md), [037-pr-retry-private-message-fetches.md](037-pr-retry-private-message-fetches.md), [054-pr-deduplicate-private-message-detail-fetches.md](054-pr-deduplicate-private-message-detail-fetches.md), [067-pr-deduplicate-direct-private-message-fetches.md](067-pr-deduplicate-direct-private-message-fetches.md), [077-pr-skip-empty-private-message-fetch-batches.md](077-pr-skip-empty-private-message-fetch-batches.md), [133-pr-reuse-private-message-list-first-page-body.md](133-pr-reuse-private-message-list-first-page-body.md), [163-pr-private-message-list-row-error-context.md](163-pr-private-message-list-row-error-context.md), and [178-pr-private-message-list-fetch-failure-context.md](178-pr-private-message-list-fetch-failure-context.md).

## Changes

- Parse private-message list `data-href` values with `urlsplit(...)`.
- Accept message IDs only from the dashboard message-view route path `account/messages/view/<id>`.
- Reject non-HTTP(S) schemes such as `javascript:` and `mailto:` when a digit-bearing value would otherwise be accepted.
- Reject `http` or `https` values that do not include a host, such as `http:account/messages/view/123`.
- Reject absolute `data-href` values whose host is not `www.wikidot.com`.
- Preserve valid relative dashboard routes and absolute `www.wikidot.com` HTTP(S) dashboard routes.
- Preserve existing no-digit `Message ID is not found ...` diagnostics, digit-bearing malformed-ID diagnostics, pagination, retry behavior, first-page body reuse, nested-row filtering, pager filtering, ordered deduplication, detail fetch delegation, inbox/sent wrappers, direct message lookup, detail parsing, and send behavior.

## Type Of Change

- Bug fix
- Private-message parser route-shape validation
- Regression tests

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | A generated private-message list `data-href` with a non-HTTP(S) scheme such as `javascript:` or `mailto:` must fail before `PrivateMessageCollection.from_ids(...)` is called. |
| R2 | An `http` or `https` `data-href` without a host must fail before `PrivateMessageCollection.from_ids(...)` is called. |
| R3 | An absolute `data-href` whose host is not `www.wikidot.com` must fail before `PrivateMessageCollection.from_ids(...)` is called. |
| R4 | A digit-bearing route that is not `account/messages/view/<id>` must fail before `PrivateMessageCollection.from_ids(...)` is called. |
| R5 | Malformed `data-href` diagnostics must include dashboard module, list page, structural row, and the observed value. |
| R6 | Valid relative dashboard message-view routes must continue to parse the same message IDs. |
| R7 | Valid absolute `www.wikidot.com` HTTP(S) message-view routes must continue to parse the same message IDs. |
| R8 | Existing no-digit diagnostics, malformed embedded-ID segment diagnostics, pagination, retry behavior, response-body diagnostics, nested-row filtering, pager filtering, ordered deduplication, detail fetch delegation, wrappers, direct lookups, detail parsing, and send behavior must remain compatible. |
| R9 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private message subjects/bodies, raw private list HTML, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R10 | Focused RED/GREEN, private-message tests, adjacent private-message/client/user/parser tests, full unit tests, lint, format, type, pyright, and whitespace gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | `javascript:/account/messages/view/123` and `mailto:account/messages/view/123` raise `NoElementException` before detail fetch delegation. | The focused RED failed with `DID NOT RAISE`; focused GREEN passed after route validation. | Calling `from_ids(...)`, storing message ID `123`, or silently dropping the row rejects this local completion claim. | Private-message list parser | `src/wikidot/module/private_message.py`, `tests/unit/test_private_message.py` |
| R2 | `http:account/messages/view/123` raises the contextual malformed-ID error. | The parametrized malformed-route regression covers hostless HTTP. | Treating hostless HTTP text as a valid relative dashboard route rejects this local completion claim. | Private-message list parser | private-message tests |
| R3 | `http://example.com/account/messages/view/123` and `https://other-site.wikidot.com/account/messages/view/123` raise the contextual malformed-ID error. | The parametrized malformed-route regression covers foreign absolute and other-site Wikidot hosts. | Extracting private-message IDs from non-dashboard hosts rejects this local completion claim. | Private-message list parser | private-message tests |
| R4 | `/account/messages/read/123` and `/other/messages/view/123` raise the contextual malformed-ID error. | The parametrized malformed-route regression covers non-message-view and non-account routes. | Accepting a numeric segment from an unrelated route rejects this local completion claim. | Private-message list parser | private-message tests |
| R5 | The malformed-route diagnostic includes module, page, row, and raw `data-href` value. | The regression matches `Message ID is malformed in data-href: <value> for module: dashboard/messages/DMInboxModule (page=1, row=1)`. | Omitting structural location or the observed value rejects this local completion claim. | Parser diagnostics | private-message tests |
| R6 | `/account/messages/view/123` still parses message ID `123`. | Existing valid acquisition tests passed in focused-nearby, private-message, and full-unit coverage. | Rejecting valid relative dashboard list routes or changing parsed IDs rejects this local completion claim. | Relative data-href compatibility | private-message tests |
| R7 | `https://www.wikidot.com/account/messages/view/123?from=list#row` still parses message ID `123`. | `test_acquire_preserves_wikidot_absolute_message_href` passed. | Rejecting absolute Wikidot dashboard message-view routes rejects this local completion claim. | Absolute dashboard data-href compatibility | private-message tests |
| R8 | Existing private-message and adjacent workflows remain green. | Focused-nearby tests, full `test_private_message.py`, adjacent private-message/client/user/parser tests, and full unit tests passed. | Regressing no-ID diagnostics, embedded-ID diagnostics, response-body diagnostics, pagination, first-page reuse, nested-row/pager filtering, deduplication, direct message lookups, detail parsing, wrappers, client accessors, or sends rejects this local completion claim. | Private-message workflows | `tests/unit` |
| R9 | No live site state or private material is needed. | All regressions use synthetic unit-level dashboard list HTML and mocked AMC responses. | Using credentials, cookies, auth JSON, raw private payloads, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, private message subjects, private message bodies, real usernames, or account data rejects this local completion claim. | Test and draft privacy | this draft |
| R10 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN, private-message tests, adjacent tests, full unit, ruff, format, mypy, pyright, and whitespace checks passed. | Test, lint, format, type, pyright, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `3b98817 fix(private_message): validate list data href routes`.

- RED: `uv run pytest tests/unit/test_private_message.py::TestPrivateMessageCollection::test_acquire_rejects_malformed_message_href_routes tests/unit/test_private_message.py::TestPrivateMessageCollection::test_acquire_preserves_wikidot_absolute_message_href -q` failed before the fix with seven `DID NOT RAISE` malformed-route cases and one passing Wikidot absolute URL compatibility case.
- GREEN focused: `uv run pytest tests/unit/test_private_message.py::TestPrivateMessageCollection::test_acquire_rejects_malformed_message_href_routes tests/unit/test_private_message.py::TestPrivateMessageCollection::test_acquire_preserves_wikidot_absolute_message_href -q` passed 8 tests.
- GREEN focused-nearby: `uv run pytest tests/unit/test_private_message.py::TestPrivateMessageCollection::test_acquire_rejects_malformed_message_href_routes tests/unit/test_private_message.py::TestPrivateMessageCollection::test_acquire_preserves_wikidot_absolute_message_href tests/unit/test_private_message.py::TestPrivateMessageCollection::test_acquire_malformed_message_href_raises tests/unit/test_private_message.py::TestPrivateMessageCollection::test_acquire_rejects_message_href_with_embedded_id_segment tests/unit/test_private_message.py::TestPrivateMessageCollection::test_acquire_ignores_non_numeric_pager_targets tests/unit/test_private_message.py::TestPrivateMessageCollection::test_acquire_reuses_first_page_body_for_message_ids tests/unit/test_private_message.py::TestPrivateMessageCollection::test_acquire_deduplicates_message_ids_preserving_order -q` passed 13 tests.
- `uv run pytest tests/unit/test_private_message.py -q` passed 177 tests.
- `uv run pytest tests/unit/test_private_message.py tests/unit/test_client.py tests/unit/test_user.py tests/unit/parsers/test_user_parser.py -q` passed 366 tests.
- `uv run pytest tests/unit -q` passed 3742 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `uv run mypy . --install-types --non-interactive` passed with no issues in 87 source files, plus existing annotation notes.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `PrivateMessageCollection._acquire(...)` raises contextual `NoElementException` for `http://example.com/account/messages/view/123`.
- `PrivateMessageCollection._acquire(...)` raises the same diagnostic family for `https://other-site.wikidot.com/account/messages/view/123`.
- `PrivateMessageCollection._acquire(...)` raises the same diagnostic family for `http:account/messages/view/123`.
- `PrivateMessageCollection._acquire(...)` raises the same diagnostic family for `javascript:/account/messages/view/123`.
- `PrivateMessageCollection._acquire(...)` raises the same diagnostic family for `mailto:account/messages/view/123`.
- `PrivateMessageCollection._acquire(...)` raises the same diagnostic family for `/account/messages/read/123`.
- `PrivateMessageCollection._acquire(...)` raises the same diagnostic family for `/other/messages/view/123`.
- The malformed-route error includes dashboard module, list page number, structural row number, and raw `data-href` value.
- Valid relative dashboard message links such as `/account/messages/view/123` still parse the same message ID.
- Valid absolute dashboard message links such as `https://www.wikidot.com/account/messages/view/123?from=list#row` still parse the same message ID.
- Existing no-digit behavior remains on the `Message ID is not found ...` path.
- Existing embedded non-ID segment behavior remains on the `Message ID is malformed ...` path.
- Existing pagination, retry handling, first-page body reuse, response-body validation, nested-row filtering, pager filtering, duplicate ID deduplication, detail fetch delegation, inbox/sent wrappers, direct message lookup, detail parser behavior, client accessors, and send behavior remain unchanged.
- No live Wikidot action, credential, cookie, auth JSON, upstream Issue, upstream PR, push, raw real private-message list HTML, raw rollout path, private message subject/body, real username, or account data is required for this local draft.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread HTML report and complexity memo are refreshed after the docs commit.
- Secret and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: Tightening private-message `data-href` parsing could reject an unusual but valid generated dashboard link. Mitigation: relative dashboard message-view links remain supported, absolute `www.wikidot.com` HTTP(S) links remain supported, and the validation only rejects foreign hosts, hostless HTTP(S), non-HTTP(S) schemes, or non-message-view routes when a digit-bearing value would otherwise be accepted.
- Risk: This could be confused with Issue 728. Mitigation: Issue 728 validates the terminal numeric segment shape; this slice validates route scheme, host, and dashboard path before accepting an otherwise valid numeric segment.
- Risk: This could blur existing missing-ID diagnostics. Mitigation: `data-href` values without any digits still use `Message ID is not found ...`; digit-bearing malformed routes use `Message ID is malformed ...`.
- Risk: Diagnostics could expose raw private message payloads. Mitigation: the diagnostic reports only the scalar `data-href` value plus module/page/row context, not response bodies, credentials, cookies, message subjects, message bodies, local paths, or account data.

## Dependencies

- Dashboard private-message list modules continue to represent message detail links as relative `/account/messages/view/<id>` routes or `www.wikidot.com` HTTP(S) routes.
- `PrivateMessage.id` remains a parsed integer message identity; direct constructor and direct lookup validation are unchanged.
- `PrivateMessageCollection._acquire(...)` remains the internal list parser used by `PrivateMessageInbox.acquire(...)` and `PrivateMessageSentBox.acquire(...)`.

## Open Questions

None for this local slice. Future private-message parser changes should be selected only after a fresh duplicate check and public RED test.

## Upstream-Safe Motivation

Private-message IDs are durable identity metadata for browser-free inbox/sent-box reads, notification ledgers, moderation workflows, migration checks, generated fixtures, and client accessors. A list-row `data-href` from another host, a non-HTTP scheme, a hostless HTTP string, or an unrelated dashboard route is not a private-message detail route. Validating route shape keeps malformed module output visible while preserving normal relative and `www.wikidot.com` dashboard links.

## Local Evidence, Not For Upstream Paste

- The focused RED test demonstrated prior behavior: seven malformed present `data-href` routes did not raise and were accepted as message ID `123`.
- Existing local drafts covered retry behavior, duplicate detail fetching, direct empty/direct ID behavior, first-page reuse, row diagnostics, response-body typing, missing/no-ID `data-href` diagnostics, embedded non-ID segment diagnostics, detail parser diagnostics, constructor fields, retained message ID state, and send action validation; they did not validate present generated list `data-href` route/scheme/host shape before `PrivateMessage.id` is fetched.
- This slice does not change request payloads, retry policy, message row selectors, list pagination, first-page response reuse, nested-row/pager filtering, duplicate ID handling, detail fetch response parsing, direct `PrivateMessage` constructor rules, inbox/sent wrapper behavior, live Wikidot behavior, upstream filing state, or valid relative/`www.wikidot.com` HTTP(S) dashboard output.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, cookies, auth JSON, generated private-message list HTML from real accounts, private message subjects, private message bodies, real usernames, and live account data out of upstream discussion.
