# PR Draft: Validate Private Message Pager Page ASCII Shape

## Summary

`PrivateMessageCollection._acquire(...)` parses the first inbox or sent-box list response pager to decide whether additional private-message list pages should be fetched. The current pager scan uses `page_text.isdigit()` before `int(page_text)`, so generated labels containing Unicode digit glyphs such as `"\uff12"` are accepted and normalized into ordinary page number `2`. That can turn malformed generated pager metadata into a real follow-up dashboard request.

This change accepts private-message list pager page labels only when they match ASCII digits. Ordinary non-numeric pager labels such as `next` continue to be ignored, valid ASCII pagination still fetches subsequent pages, row-local pager markup remains scoped away from the response-wide pager, and digit-like non-ASCII labels now fail with `NoElementException("Message list pager page is malformed ...")` including module, page, field, and observed value context.

## Outcome

Inbox and sent-box acquisition no longer fabricates pagination traversal from malformed generated pager labels. A private-message list response with fullwidth, Arabic-Indic, superscript, or other non-ASCII digit-like pager text now fails at the pager boundary instead of issuing unintended extra page requests.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators using browser-free private-message inbox or sent-box reads, moderation ledgers, migration checks, notification audits, local fixtures, or generated workflows where page traversal must come only from structurally valid Wikidot pager metadata.

## Current Evidence

Local rollout-backed drafts repeatedly identify private-message reads as a practical workflow surface. Existing drafts cover retry-aware private-message fetching, duplicate detail reduction, first-page body reuse, row-local pager filtering, nested-row filtering, response-body diagnostics, row parser diagnostics, private-message data-href route and ID shape diagnostics, direct message ID validation, retained record validation, and send-side validation.

This slice is not a duplicate of [101-pr-ignore-private-message-row-pager-markup.md](101-pr-ignore-private-message-row-pager-markup.md), which protects message-row content from being mistaken for the response-wide pager. It is not a duplicate of [133-pr-reuse-private-message-list-first-page-body.md](133-pr-reuse-private-message-list-first-page-body.md), [178-pr-private-message-list-fetch-failure-context.md](178-pr-private-message-list-fetch-failure-context.md), or [207-pr-private-message-list-response-body-context.md](207-pr-private-message-list-response-body-context.md), which cover list fetch/body behavior around pager parsing. It is not a duplicate of [728-pr-validate-private-message-data-href-id-shape.md](728-pr-validate-private-message-data-href-id-shape.md), [742-pr-validate-private-message-data-href-routes.md](742-pr-validate-private-message-data-href-routes.md), or [745-pr-validate-private-message-data-href-id-ascii-shape.md](745-pr-validate-private-message-data-href-id-ascii-shape.md), which validate row `data-href` message identity after list pagination has already been chosen.

No upstream issue was filed from this local workspace.

## Related Issues

Builds on [037-pr-retry-private-message-fetches.md](037-pr-retry-private-message-fetches.md), [054-pr-deduplicate-private-message-detail-fetches.md](054-pr-deduplicate-private-message-detail-fetches.md), [073-pr-reuse-private-message-detail-parsing.md](073-pr-reuse-private-message-detail-parsing.md), [077-pr-skip-empty-private-message-fetch-batches.md](077-pr-skip-empty-private-message-fetch-batches.md), [101-pr-ignore-private-message-row-pager-markup.md](101-pr-ignore-private-message-row-pager-markup.md), [102-pr-ignore-private-message-nested-row-markup.md](102-pr-ignore-private-message-nested-row-markup.md), [133-pr-reuse-private-message-list-first-page-body.md](133-pr-reuse-private-message-list-first-page-body.md), [163-pr-private-message-list-row-error-context.md](163-pr-private-message-list-row-error-context.md), [178-pr-private-message-list-fetch-failure-context.md](178-pr-private-message-list-fetch-failure-context.md), [207-pr-private-message-list-response-body-context.md](207-pr-private-message-list-response-body-context.md), [321-pr-private-message-response-body-type-context.md](321-pr-private-message-response-body-type-context.md), [397-pr-validate-private-message-retry-controls.md](397-pr-validate-private-message-retry-controls.md), [643-pr-validate-non-negative-private-message-ids.md](643-pr-validate-non-negative-private-message-ids.md), [674-pr-validate-private-message-collection-retained-id-state.md](674-pr-validate-private-message-collection-retained-id-state.md), [728-pr-validate-private-message-data-href-id-shape.md](728-pr-validate-private-message-data-href-id-shape.md), [742-pr-validate-private-message-data-href-routes.md](742-pr-validate-private-message-data-href-routes.md), [745-pr-validate-private-message-data-href-id-ascii-shape.md](745-pr-validate-private-message-data-href-id-ascii-shape.md), and the adjacent response-wide pager-page draft [750-pr-validate-site-member-pager-page-ascii-shape.md](750-pr-validate-site-member-pager-page-ascii-shape.md).

## Changes

- Add a local pager-page parser for `PrivateMessageCollection._acquire(...)` that accepts only `[0-9]+` before integer conversion.
- Raise `NoElementException` with module, first-page, field, and observed value context when a pager label is digit-like but not ASCII digits.
- Preserve ordinary non-numeric pager labels, missing pager behavior, valid ASCII pagination, paginated retry exhaustion handling, list response-body diagnostics, message-row parsing, row-local pager filtering, nested-row filtering, duplicate message-ID deduplication, detail fetch delegation, inbox/sent-box wrappers, and send behavior.
- Add focused regression coverage for a response-wide private-message list pager containing fullwidth page label `"\uff12"`.

## Type Of Change

- Bug fix
- Private-message list pager scalar-shape validation
- Regression test

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | A response-wide private-message list pager label containing non-ASCII digit glyphs must fail before any extra page request is issued. |
| R2 | The malformed pager diagnostic must include module, page, field, and observed value context. |
| R3 | Valid ASCII pager labels must continue to fetch subsequent private-message list pages. |
| R4 | Ordinary non-numeric pager labels such as `next` must continue to be ignored. |
| R5 | Message-row-local pager markup must continue to be ignored as row content, not response pagination. |
| R6 | Existing list response-body, retry-exhaustion, nested-row, duplicate-ID, data-href, detail fetch, inbox/sent-box, direct read, and send workflows must remain compatible. |
| R7 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private-message subjects, private-message bodies, raw generated HTML from real accounts, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R8 | Focused RED/GREEN, private-message tests, full unit tests, lint, format, type, pyright, whitespace, focused Brooks review, and Clawpatch doctor gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | `"\uff12"` in the response-wide pager raises before a page-2 request can be made. | `test_acquire_rejects_non_ascii_digit_pager_target` failed RED with `DID NOT RAISE`, then passed after ASCII-only pager parsing. | Returning messages, normalizing `"\uff12"` into page `2`, issuing a second request, or silently dropping the malformed digit rejects this local completion claim. | Private-message list pager parser | `src/wikidot/module/private_message.py`, `tests/unit/test_private_message.py` |
| R2 | The exception reports `Message list pager page is malformed for module: dashboard/messages/DMInboxModule, page: 1 (field=page, value=\uff12)`. | The focused regression asserts the exact diagnostic family and contextual fields. | A raw `ValueError`, omitted module/page context, omitted scalar value, or unrelated message-row diagnostic rejects this local completion claim. | Pager diagnostics | focused test |
| R3 | Valid ASCII pager label `2` still fetches page 2 and deduplicates message IDs across pages. | Focused GREEN included `test_acquire_deduplicates_message_ids_preserving_order`. | Failing to fetch page 2, changing request payloads, or returning only first-page IDs rejects this local completion claim. | Valid pagination | private-message pagination tests |
| R4 | `next` remains ignored when no numeric page label exists. | Focused GREEN included `test_acquire_ignores_non_numeric_pager_targets`. | Raising for `next` or making a synthetic extra request rejects this local completion claim. | Non-numeric pager compatibility | private-message pager tests |
| R5 | Pager-like markup inside a message row remains scoped away from response pagination. | Focused GREEN included `test_acquire_ignores_message_row_pager_markup`. | Treating message-row content as response pagination or issuing a page-2 request rejects this local completion claim. | Row scoping | private-message row-pager test |
| R6 | Adjacent private-message workflows remain green. | `tests/unit/test_private_message.py` passed 179 tests, and full unit passed 3752 tests. | Regressing first-page retry exhaustion, paginated retry exhaustion, response-body diagnostics, nested-row filtering, data-href validation, duplicate-ID deduplication, detail fetch delegation, inbox/sent-box wrappers, direct reads, sends, or any unit test rejects this local completion claim. | Private-message workflows | `tests/unit` |
| R7 | No live site state or private material is needed. | The regression uses synthetic unit-level private-message list HTML and mock AMC responses. | Using credentials, cookies, auth JSON, raw private payloads, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, real account names, private-message subjects, private-message bodies, or raw generated HTML from real accounts rejects this local completion claim. | Test and draft privacy | this draft |
| R8 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN, private-message tests, full unit, ruff, format, mypy, pyright, whitespace, focused Brooks review, and Clawpatch doctor checks passed. | Test, lint, format, type, pyright, whitespace, review, doctor, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `5b82597 fix(private_message): validate pager page shape`.

- RED: `uv run --extra test pytest tests/unit/test_private_message.py::TestPrivateMessageCollection::test_acquire_rejects_non_ascii_digit_pager_target -q` failed before the fix with `DID NOT RAISE` because pager label `"\uff12"` was accepted and normalized as page `2`.
- GREEN focused: `uv run --extra test pytest tests/unit/test_private_message.py::TestPrivateMessageCollection::test_acquire_rejects_non_ascii_digit_pager_target -q` passed 1 test.
- GREEN adjacent pager slice: `uv run --extra test pytest tests/unit/test_private_message.py::TestPrivateMessageCollection::test_acquire_ignores_non_numeric_pager_targets tests/unit/test_private_message.py::TestPrivateMessageCollection::test_acquire_ignores_message_row_pager_markup tests/unit/test_private_message.py::TestPrivateMessageCollection::test_acquire_deduplicates_message_ids_preserving_order -q` passed 3 tests.
- `uv run --extra test pytest tests/unit/test_private_message.py -q` passed 179 tests.
- `uv run --extra test pytest tests/unit/ -q` passed 3752 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `uv run mypy . --install-types --non-interactive` passed with no issues in 87 source files, plus existing annotation notes.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.
- Focused Brooks changed-file review found no private-message pager-boundary, compatibility, architecture, or test-decay findings; the full autonomous Brooks sweep was not run because the skill gates broad repository auto-fix behind explicit user consent.
- Clawpatch doctor evidence was collected without starting a review worker: `provider=codex`, `state=missing`, `providerVersion="codex-cli 0.138.0-alpha.6"`, launcher SHA256 `0518e09af8c6a44990de082462039c9593a8f969a8e0eb10426aa6b3dcf630be`.

## Acceptance Criteria

- `PrivateMessageCollection._acquire(client, "dashboard/messages/DMInboxModule")` raises `NoElementException("Message list pager page is malformed ...")` for a response-wide pager label whose text is `"\uff12"`.
- The malformed pager diagnostic includes `module: dashboard/messages/DMInboxModule`, `page: 1`, `field=page`, and `value=\uff12` context.
- The parser does not issue a page-2 private-message list request from non-ASCII digit pager text.
- Valid ASCII response-wide pager labels such as `2` still fetch and parse paginated message lists.
- Ordinary non-numeric pager labels such as `next` still leave the message list as a single-page result when no numeric page label exists.
- Message-row-local pager-like markup is still ignored as row content and does not drive response-wide pagination.
- Existing private-message list response-body diagnostics, retry-exhaustion behavior, nested-row filtering, data-href validation, duplicate-ID deduplication, direct reads, detail fetch delegation, inbox/sent-box wrappers, sends, and full unit behavior remain green.
- No live Wikidot action, credential, cookie, auth JSON, upstream Issue, upstream PR, push, raw generated HTML from real accounts, raw rollout path, real account name, private-message subject, private-message body, or private site detail is required for this local draft.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread HTML report and complexity memo are refreshed after the docs commit.
- Secret and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: This could be confused with row-local pager scoping. Mitigation: row-local pager markup remains covered by Issue 101; this slice validates response-wide pager page-label shape after pager selection.
- Risk: This could be confused with private-message `data-href` ID validation. Mitigation: `data-href` route and ID shape remain covered by Issues 728, 742, and 745; this slice runs before message-row IDs are parsed.
- Risk: This could break ordinary pager labels such as `next`. Mitigation: non-numeric labels are still ignored; only digit-like non-ASCII labels that the old code treated as numeric now fail.
- Risk: This could break valid pagination. Mitigation: ASCII `[0-9]+` labels still convert to integers, and the existing paginated acquisition test remains green.
- Risk: Diagnostics could expose private message content. Mitigation: the new diagnostic includes only module/page context and the malformed pager scalar; tests use synthetic HTML and do not include real message subjects, previews, bodies, or account names.
- Risk: Another digit-like Unicode category could behave differently than fullwidth digits. Mitigation: the code rejects any `str.isdigit()` value that does not match ASCII digits, covering fullwidth, superscript, Arabic-Indic, and similar digit glyphs.

## Dependencies

- BeautifulSoup continues to expose generated pager target text through `get_text(strip=True)`.
- Normal Wikidot private-message list pager page labels are expected to be ASCII decimal digits.
- `PrivateMessageCollection._pager_targets_from_html(...)` continues to scope the response-wide pager before page-number parsing.
- `PrivateMessageCollection._message_list_response_body(...)` continues to validate first and paginated response bodies before pager and row parsing.

## Open Questions

None for this local slice. Future private-message pagination changes should be selected only after a fresh duplicate check and public RED test.

## Upstream-Safe Motivation

Private-message list pagination is a browser-free acquisition boundary. Unicode digit normalization can silently turn malformed generated pager text into a valid-looking page request, which is surprising and hard to diagnose in inbox or sent-box ledgers. Requiring ASCII digits keeps generated pagination strict while preserving valid Wikidot pager behavior and existing parser diagnostics.

## Local Evidence, Not For Upstream Paste

- The focused RED test demonstrated prior behavior: fullwidth digit pager text was accepted and normalized into page `2`.
- Existing local drafts covered private-message retries, duplicate detail reduction, first-page body reuse, row scoping, row-pager filtering, nested-row filtering, response-body diagnostics, row parser diagnostics, data-href route and ID validation, direct message ID validation, retained record validation, and send-side validation; they did not validate Unicode digit normalization in response-wide private-message list pager labels.
- This slice does not change request module names, retry policy, valid ASCII pagination, first-page parsing, paginated response-body diagnostics, row parsing, `data-href` parsing, duplicate message-ID deduplication, detail fetch delegation, inbox/sent-box wrappers, direct reads, sends, live Wikidot behavior, or upstream filing state.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, cookies, auth JSON, generated HTML from real accounts, real account names, private-message subjects, private-message bodies, private site data, and private page source out of upstream discussion.
