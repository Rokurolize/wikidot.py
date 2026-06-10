# PR Draft: Validate Site Member Pager Page ASCII Shape

## Summary

`SiteMember.get(...)` parses the generated membership `MembersListModule` pager after the first page to decide whether additional member-list pages should be fetched. The current pager scan uses `page_text.isdigit()` before `int(page_text)`, so generated labels containing Unicode digit glyphs such as `"\uff12"` are accepted and normalized into ordinary page number `2`. That can turn malformed generated pager metadata into a real second-page request.

This change accepts pager page labels only when they match ASCII digits. Ordinary non-numeric pager links such as `next` continue to be ignored, valid ASCII pagination still fetches subsequent pages, and digit-like non-ASCII labels now fail with `NoElementException("Site member pager page is malformed ...")` including site, group, page, field, and observed value context.

## Outcome

Browser-free member-list acquisition no longer fabricates pagination traversal from malformed generated pager labels. A member-list response with fullwidth, Arabic-Indic, superscript, or other non-ASCII digit-like pager text now fails at the pager boundary instead of issuing unintended follow-up requests.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators using site membership reads, membership ledgers, role audits, moderation workflows, migration scripts, translation-review tooling, or generated fixtures where page traversal must come only from structurally valid Wikidot pager metadata.

## Current Evidence

Local rollout-backed drafts repeatedly identify site membership reads and administration as practical workflows. Existing drafts cover retry-aware member-list fetching, row-scoped parsing, row-local pager markup filtering, first and paginated response-body diagnostics, malformed member user and joined-at diagnostics, action response validation, action-user preflight, member lookup validation, constructor state validation, member/site coherence, and adjacent generated scalar ASCII-shape validation.

This slice is not a duplicate of [103-pr-ignore-site-member-row-pager-markup.md](103-pr-ignore-site-member-row-pager-markup.md), which protects member-row content from being mistaken for the response-wide pager. It is not a duplicate of [213-pr-site-member-list-response-body-context.md](213-pr-site-member-list-response-body-context.md), [289-pr-site-member-user-context.md](289-pr-site-member-user-context.md), [290-pr-site-member-joined-at-context.md](290-pr-site-member-joined-at-context.md), or [323-pr-site-member-response-body-type-context.md](323-pr-site-member-response-body-type-context.md), which cover response and row parser diagnostics. This slice covers the accepted-value shape of response-wide pager page numbers after the pager has already been selected.

No upstream issue was filed from this local workspace.

## Related Issues

Builds on [031-pr-retry-member-list-fetches.md](031-pr-retry-member-list-fetches.md), [096-pr-scope-site-member-row-parsing.md](096-pr-scope-site-member-row-parsing.md), [103-pr-ignore-site-member-row-pager-markup.md](103-pr-ignore-site-member-row-pager-markup.md), [176-pr-site-member-fetch-failure-context.md](176-pr-site-member-fetch-failure-context.md), [213-pr-site-member-list-response-body-context.md](213-pr-site-member-list-response-body-context.md), [289-pr-site-member-user-context.md](289-pr-site-member-user-context.md), [290-pr-site-member-joined-at-context.md](290-pr-site-member-joined-at-context.md), [323-pr-site-member-response-body-type-context.md](323-pr-site-member-response-body-type-context.md), [357-pr-validate-site-member-lookup-username.md](357-pr-validate-site-member-lookup-username.md), [372-pr-validate-site-member-lookup-user-id.md](372-pr-validate-site-member-lookup-user-id.md), [410-pr-validate-site-member-action-users.md](410-pr-validate-site-member-action-users.md), [541-pr-validate-site-member-get-site.md](541-pr-validate-site-member-get-site.md), [688-pr-validate-site-member-action-user-id-range.md](688-pr-validate-site-member-action-user-id-range.md), [690-pr-validate-site-member-constructor-user-id-range.md](690-pr-validate-site-member-constructor-user-id-range.md), [700-pr-validate-site-member-constructor-user-id-state.md](700-pr-validate-site-member-constructor-user-id-state.md), and the adjacent ASCII-shape drafts [743-pr-validate-forum-thread-script-id-ascii-shape.md](743-pr-validate-forum-thread-script-id-ascii-shape.md), [744-pr-validate-page-file-row-id-ascii-shape.md](744-pr-validate-page-file-row-id-ascii-shape.md), [745-pr-validate-private-message-data-href-id-ascii-shape.md](745-pr-validate-private-message-data-href-id-ascii-shape.md), [746-pr-validate-forum-category-href-id-ascii-shape.md](746-pr-validate-forum-category-href-id-ascii-shape.md), [747-pr-validate-forum-thread-href-id-ascii-shape.md](747-pr-validate-forum-thread-href-id-ascii-shape.md), [748-pr-validate-regular-user-onclick-id-ascii-shape.md](748-pr-validate-regular-user-onclick-id-ascii-shape.md), and [749-pr-validate-deleted-user-data-id-ascii-shape.md](749-pr-validate-deleted-user-data-id-ascii-shape.md).

## Changes

- Add a local pager-page parser for `SiteMember.get(...)` that accepts only `[0-9]+` before integer conversion.
- Raise `NoElementException` with site, group, first-page, field, and observed value context when a pager label is digit-like but not ASCII digits.
- Preserve ordinary non-numeric pager links, missing pager behavior, valid ASCII pagination, paginated retry exhaustion handling, response-body diagnostics, member-row parsing, row-local pager filtering, and all role/admin behavior.
- Add focused regression coverage for a response-wide site-member pager containing fullwidth page label `"\uff12"`.

## Type Of Change

- Bug fix
- Site member pager scalar-shape validation
- Regression test

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | A response-wide site-member pager label containing non-ASCII digit glyphs must fail before any extra page request is issued. |
| R2 | The malformed pager diagnostic must include site, group, page, field, and observed value context. |
| R3 | Valid ASCII pager labels must continue to fetch subsequent member-list pages. |
| R4 | Ordinary non-numeric pager labels such as `next` must continue to be ignored. |
| R5 | Member-row-local pager markup must continue to be ignored as row content, not response pagination. |
| R6 | Existing first-page and paginated response-body, retry-exhaustion, member-user, joined-at, group, lookup, role-action, and constructor workflows must remain compatible. |
| R7 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private user data, raw generated HTML from real sites, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R8 | Focused RED/GREEN, site-member tests, adjacent site/member/application/user tests, full unit tests, lint, format, type, pyright, whitespace, focused Brooks review, and Clawpatch doctor gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | `"\uff12"` in the response-wide pager raises before a page-2 request can be made. | `test_get_members_rejects_non_ascii_digit_pager_page` failed RED with `DID NOT RAISE`, then passed after ASCII-only pager parsing. | Returning members, normalizing `"\uff12"` into page `2`, issuing a second request, or silently dropping the malformed digit rejects this local completion claim. | Site-member pager parser | `src/wikidot/module/site_member.py`, `tests/unit/test_site_member.py` |
| R2 | The exception reports `Site member pager page is malformed for site: test-site, group: members, page: 1 (field=page, value=\uff12)`. | The focused regression asserts the exact diagnostic family and contextual fields. | A raw `ValueError`, omitted site/group/page context, omitted scalar value, or unrelated member-row diagnostic rejects this local completion claim. | Pager diagnostics | focused test |
| R3 | Valid ASCII pager label `2` still fetches page 2 and returns both pages' members. | Focused GREEN included `test_get_members_with_pagination`. | Failing to fetch page 2, changing request payloads, or returning only first-page members rejects this local completion claim. | Valid pagination | site-member pagination tests |
| R4 | `next` remains ignored when no numeric page label exists. | Focused GREEN included `test_get_members_ignores_non_numeric_pager_links`. | Raising for `next` or making a synthetic extra request rejects this local completion claim. | Non-numeric pager compatibility | site-member pagination tests |
| R5 | Pager-like markup inside a member row remains scoped away from response pagination. | Focused GREEN included `test_get_members_ignores_member_row_pager_markup`. | Treating member-row content as response pagination or issuing a page-2 request rejects this local completion claim. | Row scoping | site-member row-pager test |
| R6 | Adjacent site/member workflows remain green. | `tests/unit/test_site_member.py` passed 88 tests, adjacent site/member/application/user coverage passed 638 tests, and full unit passed 3751 tests. | Regressing first-page retry exhaustion, paginated retry exhaustion, response-body diagnostics, member user parsing, joined-at parsing, group payloads, site lookup, application workflows, user parsing, role actions, or any unit test rejects this local completion claim. | Site-member and adjacent workflows | `tests/unit` |
| R7 | No live site state or private material is needed. | The regression uses synthetic unit-level member-list HTML and mock AMC responses. | Using credentials, cookies, auth JSON, raw private payloads, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, real user names, private page source, private message data, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R8 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN, site-member tests, adjacent tests, full unit, ruff, format, mypy, pyright, whitespace, focused Brooks review, and Clawpatch doctor checks passed. | Test, lint, format, type, pyright, whitespace, review, doctor, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `a8c119a fix(site_member): validate pager page shape`.

- RED: `uv run --extra test pytest tests/unit/test_site_member.py::TestSiteMemberGet::test_get_members_rejects_non_ascii_digit_pager_page -q` failed before the fix with `DID NOT RAISE` because pager label `"\uff12"` was accepted and normalized as page `2`.
- GREEN focused: `uv run --extra test pytest tests/unit/test_site_member.py::TestSiteMemberGet::test_get_members_rejects_non_ascii_digit_pager_page tests/unit/test_site_member.py::TestSiteMemberGet::test_get_members_with_pagination tests/unit/test_site_member.py::TestSiteMemberGet::test_get_members_ignores_non_numeric_pager_links tests/unit/test_site_member.py::TestSiteMemberGet::test_get_members_ignores_member_row_pager_markup tests/unit/test_site_member.py::TestSiteMemberGet::test_get_members_raises_when_paginated_retry_is_exhausted tests/unit/test_site_member.py::TestSiteMemberGet::test_get_members_missing_paginated_response_body_includes_context -q` passed 6 tests.
- `uv run --extra test pytest tests/unit/test_site_member.py -q` passed 88 tests.
- `uv run --extra test pytest tests/unit/test_site_member.py tests/unit/test_site.py tests/unit/test_site_application.py tests/unit/test_user.py -q` passed 638 tests.
- `uv run --extra test pytest tests/unit -q` passed 3751 tests.
- `uv run ruff check src tests` passed.
- `uv run ruff format --check src tests` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files, plus existing annotation notes.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.
- Focused Brooks changed-file review found no site-member pager-boundary, compatibility, or test-decay findings; the full autonomous Brooks sweep was not run because the skill gates broad safe/risky cleanup behind explicit user consent.
- Clawpatch doctor evidence was collected without starting a review worker: `provider=codex`, `state=missing`, `providerVersion="codex-cli 0.138.0-alpha.6"`, launcher SHA256 `0518e09af8c6a44990de082462039c9593a8f969a8e0eb10426aa6b3dcf630be`.

## Acceptance Criteria

- `SiteMember.get(site, "")` raises `NoElementException("Site member pager page is malformed ...")` for a response-wide pager link whose text is `"\uff12"`.
- The malformed pager diagnostic includes `site: test-site`, `group: members`, `page: 1`, `field=page`, and `value=\uff12` context.
- The parser does not issue a page-2 member-list request from non-ASCII digit pager text.
- Valid ASCII response-wide pager labels such as `2` still fetch and parse paginated member lists.
- Ordinary non-numeric pager labels such as `next` still leave the member list as a single-page result when no numeric page label exists.
- Member-row-local pager-like markup is still ignored as member-row content and does not drive response-wide pagination.
- Existing member-list response-body diagnostics, retry-exhaustion behavior, group payloads, member user parsing, joined-at parsing, site/application/user tests, and full unit behavior remain green.
- No live Wikidot action, credential, cookie, auth JSON, upstream Issue, upstream PR, push, raw generated HTML from real sites, raw rollout path, real user name, private page source, private message data, or private site detail is required for this local draft.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread HTML report and complexity memo are refreshed after the docs commit.
- Secret and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: This could be confused with row-local pager scoping. Mitigation: row-local pager markup remains covered by Issue 103; this slice validates response-wide pager page-label shape after pager selection.
- Risk: This could break ordinary pager links such as `next`. Mitigation: non-numeric labels are still ignored; only digit-like non-ASCII labels that the old code treated as numeric now fail.
- Risk: This could break valid pagination. Mitigation: ASCII `[0-9]+` labels still convert to integers, and the focused pagination test remains green.
- Risk: Diagnostics could expose private membership data. Mitigation: the new diagnostic includes only site/group/page context and the malformed pager scalar; tests use synthetic HTML and do not include real member data.
- Risk: Another digit-like Unicode category could behave differently than fullwidth digits. Mitigation: the code rejects any `str.isdigit()` value that does not match ASCII digits, covering fullwidth, superscript, Arabic-Indic, and similar digit glyphs.

## Dependencies

- BeautifulSoup continues to expose generated pager link text through `get_text(strip=True)`.
- Normal Wikidot membership pager page labels are expected to be ASCII decimal digits.
- `SiteMember._pager_from_html(...)` continues to scope the response-wide pager before page-number parsing.
- `SiteMember._member_list_response_body(...)` continues to validate first and paginated response bodies before row parsing.

## Open Questions

None for this local slice. Future site-member pagination changes should be selected only after a fresh duplicate check and public RED test.

## Upstream-Safe Motivation

Site-member pagination is a browser-free acquisition boundary. Unicode digit normalization can silently turn malformed generated pager text into a valid-looking page request, which is surprising and hard to diagnose in member ledgers or role audits. Requiring ASCII digits keeps generated pagination strict while preserving valid Wikidot pager behavior and existing parser diagnostics.

## Local Evidence, Not For Upstream Paste

- The focused RED test demonstrated prior behavior: fullwidth digit pager text was accepted and normalized into page `2`.
- Existing local drafts covered member-list retries, row scoping, row-pager filtering, response-body diagnostics, member user diagnostics, joined-at diagnostics, lookup validation, role-action validation, constructor validation, and adjacent ASCII-shape scalar fixes; they did not validate Unicode digit normalization in response-wide site-member pager labels.
- This slice does not change request module names, retry policy, valid group behavior, valid ASCII pagination, first-page parsing, paginated response-body diagnostics, member-row parsing, user parsing, joined-at parsing, role actions, lookup behavior, constructor behavior, live Wikidot behavior, or upstream filing state.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, cookies, auth JSON, generated HTML from real sites, real user names, private page source, private message data, and private site data out of upstream discussion.
