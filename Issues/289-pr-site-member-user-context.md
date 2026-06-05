# PR Draft: Report Malformed Site Member List Users

## Summary

`SiteMember.get(site, group)` parses `membership/MembersListModule` rows into `SiteMember` objects for all members, admins, and moderators. Earlier local slices made this read path retry-aware, scoped member rows to direct generated table structure, ignored row-local pager markup, validated missing response bodies, added retry-exhausted site/group/page context, validated permission-change action status, and invalidated stale role caches after successful role changes. One adjacent parser-value gap remained: when a structural member row contained a present `span.printuser` whose `userInfo(...)` metadata was malformed, the shared `user_parse(...)` utility raised raw `ValueError("user id is not found")` without identifying the site, member group, page, row, affected field, or observed `onclick` value.

This follow-up keeps the shared `user_parse(...)` utility unchanged and catches malformed site-member list user metadata at the member-list parser boundary. It raises `NoElementException` with site, resolved group label, page, structural row, `field=user`, and the offending direct `onclick` value. Valid member parsing, rows without users, missing joined-at timestamps, malformed response-body handling, pagination, retry behavior, group selection, site accessors, permission-change actions, and role-cache invalidation remain unchanged.

## Related Issue

Builds on [031-pr-retry-member-list-fetches.md](031-pr-retry-member-list-fetches.md), [096-pr-scope-site-member-row-parsing.md](096-pr-scope-site-member-row-parsing.md), [103-pr-ignore-site-member-row-pager-markup.md](103-pr-ignore-site-member-row-pager-markup.md), [176-pr-site-member-fetch-failure-context.md](176-pr-site-member-fetch-failure-context.md), [213-pr-site-member-list-response-body-context.md](213-pr-site-member-list-response-body-context.md), [255-pr-site-member-change-group-action-status-context.md](255-pr-site-member-change-group-action-status-context.md), and [270-pr-site-member-role-cache-invalidation.md](270-pr-site-member-role-cache-invalidation.md). Those drafts established member-list acquisition, member row parsing, member action validation, and role-cache refresh as practical site-administration surfaces. This slice also follows the shared printuser parser-boundary pattern from [118-pr-preserve-printuser-name-spacing.md](118-pr-preserve-printuser-name-spacing.md), [285-pr-forum-post-revision-user-context.md](285-pr-forum-post-revision-user-context.md), and [288-pr-private-message-detail-user-context.md](288-pr-private-message-detail-user-context.md).

No upstream issue was filed from this local workspace.

## Changes

- Convert malformed present site-member list `span.printuser` metadata from raw `ValueError` into contextual `NoElementException`.
- Include site unix name, resolved member group label, member-list page, structural row number, `field=user`, and the observed direct `onclick` value in the parser error.
- Preserve the shared `user_parse(...)` utility behavior and parser tests.
- Preserve successful member parsing through `SiteMember.get(site, group)` and direct `SiteMember._parse(site, html)` callers.
- Preserve existing member-list response-body validation, retry-exhausted behavior, pagination, row-local pager filtering, group selection, permission mutations, and cache invalidation behavior.
- Add a focused public `SiteMember.get(site, "")` regression for a malformed member `userInfo(latest)` value.

## Type Of Change

- Bug fix / diagnostics improvement
- Site member list parser hardening
- Test update

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| A structural member-list row with malformed present `userInfo(...)` metadata fails at the site-member parser boundary. | `TestSiteMemberGet.test_get_members_malformed_user_includes_site_group_page_row_and_value_context` returns a member-list page with `userInfo(latest)` and expects `NoElementException`. | Leaking raw `ValueError`, fabricating a user, silently skipping the row, or returning a `SiteMember` rejects this local completion claim. |
| The malformed user error identifies the affected site, group, page, row, field, and observed `onclick` value. | The focused regression asserts `Site member user is malformed for site: test-site, group: members, page: 1, row: 1, field=user, value=WIKIDOT.page.listeners.userInfo(latest); return false;`. | Omitting site, group, page, row, `field=user`, or the raw `onclick` value rejects this local completion claim. |
| Existing direct `SiteMember._parse(site, html)` callers remain compatible. | Existing direct parse tests still call `_parse(site, html)` without group/page arguments and passed. | Requiring new positional parser arguments for direct callers rejects this local completion claim. |
| Existing member-list response-body, pagination, and retry behavior stay intact. | Focused GREEN included single-page, missing first-page body, paginated member-list, missing paginated body, and nested-member table tests. | Regressing response-body validation, page-2 acquisition, retry-exhausted distinction, row-local parser scoping, or valid row parsing rejects this local completion claim. |
| Existing site-member workflows remain green. | `uv run --extra test pytest tests/unit/test_site_member.py -q` passed 36 tests. | Regressions in group validation, member parsing, pager filtering, permission mutations, role-cache invalidation, or login checks reject this local completion claim. |
| Adjacent site/application/user parser workflows remain compatible. | `uv run --extra test pytest tests/unit/test_site_member.py tests/unit/test_site_application.py tests/unit/test_site.py tests/unit/parsers/test_user_parser.py tests/unit/test_user.py -q` passed 171 tests. | Regressing site accessors, pending applications, shared user parser behavior, or user models rejects this local completion claim. |
| Broad unit and static quality gates remain green in the repo dependency environment. | `uv run --extra test pytest tests/unit/ -q`; `uv run ruff check .`; `uv run ruff format --check .`; `uv run mypy src tests`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject this local completion claim. |

## Testing

Implemented locally in commit `85a9833 fix(site_member): report malformed member users`.

- RED: `uv run --extra test pytest tests/unit/test_site_member.py::TestSiteMemberGet::test_get_members_malformed_user_includes_site_group_page_row_and_value_context -q` failed before the fix with `ValueError: user id is not found`.
- GREEN: `uv run --extra test pytest tests/unit/test_site_member.py::TestSiteMemberGet::test_get_members_malformed_user_includes_site_group_page_row_and_value_context tests/unit/test_site_member.py::TestSiteMemberGet::test_get_members_single_page tests/unit/test_site_member.py::TestSiteMemberGet::test_get_members_missing_first_page_response_body_includes_context tests/unit/test_site_member.py::TestSiteMemberGet::test_get_members_with_pagination tests/unit/test_site_member.py::TestSiteMemberGet::test_get_members_missing_paginated_response_body_includes_context tests/unit/test_site_member.py::TestSiteMemberParse::test_parse_single_member tests/unit/test_site_member.py::TestSiteMemberParse::test_parse_ignores_nested_member_tables -q` passed 7 tests.
- `uv run --extra test pytest tests/unit/test_site_member.py -q` passed 36 tests.
- `uv run --extra test pytest tests/unit/test_site_member.py tests/unit/test_site_application.py tests/unit/test_site.py tests/unit/parsers/test_user_parser.py tests/unit/test_user.py -q` passed 171 tests.
- `uv run --extra test pytest tests/unit/ -q` passed 846 tests.
- `uv run ruff check .`.
- `uv run ruff format --check .`.
- `uv run mypy src tests`.
- `git diff --check`.

Not run successfully: `command -v pyright` did not find a `pyright` executable.

## Acceptance Criteria

- `SiteMember.get(site, group)` raises `NoElementException` when a member-list response has a structural member row with a direct `span.printuser` element whose `userInfo(...)` metadata cannot be parsed by the shared user parser.
- The malformed user error includes the site unix name, resolved member group label, page number, structural row number, `field=user`, and observed direct `onclick` value.
- `SiteMember._parse(site, html)` remains callable with its existing two-argument form.
- Valid member rows still parse through `user_parser(...)`.
- Rows without `span.printuser`, rows without joined-at timestamps, valid joined-at timestamps, nested member tables, row-local pager markup, response-level pagination, retry-exhausted handling, missing response-body handling, group validation, permission actions, and role-cache invalidation remain unchanged.
- No live Wikidot action, upstream Issue, upstream PR, push, raw member-list HTML, or private membership data is required for this local draft.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and the local implementation commit.
- The thread HTML report and complexity memo are refreshed after the docs commit.
- Secret and local-path leak checks over the new draft pass before finalizing the turn.

## Upstream-Safe Motivation

Member, moderator, and admin lists are practical browser-free site-administration inputs. If Wikidot emits a structural member row with malformed direct user metadata, wikidot.py should return a structured parser failure naming the affected site, group, page, row, field, and observed value instead of forcing operators to infer context from a raw shared helper exception. That keeps member-list diagnostics actionable without retaining generated member-list HTML, raw response JSON, private member data, credentials, or local rollout paths.

## Local Evidence, Not For Upstream Paste

- Earlier local drafts established `SiteMember.get(site, group)` as a retry-aware and parser-scoped read path used by `Site.members`, `Site.admins`, and `Site.moderators`.
- Recent membership workflow drafts validated malformed member-list response bodies, permission-change action status, and role-cache invalidation after successful role changes; this slice targets only the malformed-present `printuser` metadata path inside member-list parsing.
- Shared printuser work has already covered display-name spacing and parser-boundary diagnostics in forum post revisions and private-message details. Site-member lists use the same shared parser but need site/group/page/row context at their own parser boundary.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, cookies, auth JSON, raw member-list HTML, private site membership data, page names from real sites, and site contents out of upstream discussion.

## Additional Notes

This is a parser correctness and observability fix. It narrows a raw utility-parser exception into the same local exception family used by surrounding member-list response and site-administration diagnostics.
