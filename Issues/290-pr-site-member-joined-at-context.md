# PR Draft: Report Malformed Site Member Join Dates

## Summary

`SiteMember.get(site, group)` parses `membership/MembersListModule` rows into `SiteMember` objects for all members, admins, and moderators. Earlier local slices made this read path retry-aware, scoped member rows to direct generated table structure, ignored row-local pager markup, validated missing response bodies, added retry-exhausted site/group/page context, validated permission-change action status, invalidated stale role caches after successful role changes, and converted malformed member `span.printuser` metadata into contextual `NoElementException`. One adjacent parser-value gap remained: when a structural member row contained a present joined-at `span.odate` whose `time_*` metadata was malformed, the shared `odate_parse(...)` utility raised raw `ValueError` without identifying the site, member group, page, row, affected field, or observed timestamp class value.

This follow-up keeps the shared `odate_parse(...)` utility unchanged and catches malformed site-member joined-at metadata at the member-list parser boundary. It raises `NoElementException` with site, resolved group label, page, structural row, `field=joined_at`, and the offending direct `time_*` class value. Valid member parsing, rows without users, rows without joined-at timestamps, valid joined-at timestamps, malformed response-body handling, pagination, retry behavior, group selection, site accessors, permission-change actions, and role-cache invalidation remain unchanged.

## Outcome

Malformed present joined-at metadata in a generated site-member row is now reported as a site-member parser failure instead of a raw shared-parser failure.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use `Site.members`, `Site.admins`, `Site.moderators`, or direct `SiteMember.get(site, group)` calls for browser-free site administration.

## Related Issue

Builds on [031-pr-retry-member-list-fetches.md](031-pr-retry-member-list-fetches.md), [096-pr-scope-site-member-row-parsing.md](096-pr-scope-site-member-row-parsing.md), [103-pr-ignore-site-member-row-pager-markup.md](103-pr-ignore-site-member-row-pager-markup.md), [176-pr-site-member-fetch-failure-context.md](176-pr-site-member-fetch-failure-context.md), [213-pr-site-member-list-response-body-context.md](213-pr-site-member-list-response-body-context.md), [255-pr-site-member-change-group-action-status-context.md](255-pr-site-member-change-group-action-status-context.md), [270-pr-site-member-role-cache-invalidation.md](270-pr-site-member-role-cache-invalidation.md), and [289-pr-site-member-user-context.md](289-pr-site-member-user-context.md). Those drafts established member-list acquisition, member row parsing, member action validation, role-cache refresh, and malformed member-user diagnostics as practical site-administration surfaces. This slice also follows the shared odate parser-boundary pattern from [282-pr-recent-change-timestamp-value-context.md](282-pr-recent-change-timestamp-value-context.md), [284-pr-forum-post-revision-timestamp-context.md](284-pr-forum-post-revision-timestamp-context.md), and [287-pr-private-message-detail-timestamp-value-context.md](287-pr-private-message-detail-timestamp-value-context.md).

No upstream issue was filed from this local workspace.

## Changes

- Convert malformed present site-member list joined-at `span.odate` metadata from raw `ValueError` into contextual `NoElementException`.
- Include site unix name, resolved member group label, member-list page, structural row number, `field=joined_at`, and the observed direct `time_*` class value in the parser error.
- Preserve the shared `odate_parse(...)` utility behavior and parser tests.
- Preserve successful member parsing through `SiteMember.get(site, group)` and direct `SiteMember._parse(site, html)` callers.
- Preserve rows without joined-at timestamps as `joined_at=None`.
- Preserve existing member-list response-body validation, retry-exhausted behavior, pagination, row-local pager filtering, group selection, permission mutations, and cache invalidation behavior.
- Add a focused public `SiteMember.get(site, "")` regression for a malformed member `class="odate time_latest"` value.

## Type Of Change

- Bug fix / diagnostics improvement
- Site member list parser hardening
- Test update

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | A structural member-list row with a present joined-at `span.odate` whose `time_*` metadata cannot be parsed must fail at the site-member parser boundary. |
| R2 | The malformed joined-at error must identify the affected site, group, page, row, field, and observed timestamp class value. |
| R3 | Existing direct `SiteMember._parse(site, html)` callers must remain compatible. |
| R4 | Existing valid member-list behavior, response handling, pagination, retries, group selection, permission mutations, and cache invalidation must remain unchanged. |
| R5 | Broad unit, lint, format, type, and whitespace gates must remain green before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | `SiteMember.get(site, "")` raises `NoElementException` for `class="odate time_latest"` in a structural member row. | `TestSiteMemberGet.test_get_members_malformed_joined_at_includes_site_group_page_row_and_value_context` returns that member-list page and expects `NoElementException`. | Leaking raw `ValueError`, fabricating a timestamp, silently returning `joined_at=None`, skipping the row, or returning a `SiteMember` rejects this local completion claim. | `src/wikidot/module/site_member.py` | `tests/unit/test_site_member.py` |
| R2 | The error names site, group, page, row, `field=joined_at`, and `value=time_latest`. | The focused regression asserts `Site member joined_at is malformed for site: test-site, group: members, page: 1, row: 1, field=joined_at, value=time_latest`. | Omitting any location field, using only the rendered date text, or hiding the raw class value rejects this local completion claim. | `SiteMember.get(site, group)` diagnostics | `tests/unit/test_site_member.py` |
| R3 | `SiteMember._parse(site, html)` stays callable with its existing two-argument form. | Existing direct parse tests still call `_parse(site, html)` without group/page arguments and passed. | Requiring new positional parser arguments for direct callers rejects this local completion claim. | `SiteMember._parse(...)` | `tests/unit/test_site_member.py` |
| R4 | Valid and adjacent member-list workflows stay green. | Focused GREEN included malformed user, single-page, direct valid parse, and nested-member table tests; full `tests/unit/test_site_member.py` passed 37 tests. | Regressing valid joined-at parsing, missing joined-at behavior, response-body validation, page-2 acquisition, retry-exhausted distinction, row-local parser scoping, or permission/cache behavior rejects this local completion claim. | Site member list workflows | `tests/unit/test_site_member.py` |
| R5 | Repository quality gates pass in the local dependency environment. | Full unit suite and static checks passed before the code commit. | Test, lint, format, type, or whitespace failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `bc239e5 fix(site_member): report malformed member join dates`.

- RED: `uv run --extra test pytest tests/unit/test_site_member.py::TestSiteMemberGet::test_get_members_malformed_joined_at_includes_site_group_page_row_and_value_context -q` failed before the fix with `ValueError: invalid literal for int() with base 10: 'latest'`.
- GREEN: `uv run --extra test pytest tests/unit/test_site_member.py::TestSiteMemberGet::test_get_members_malformed_joined_at_includes_site_group_page_row_and_value_context tests/unit/test_site_member.py::TestSiteMemberGet::test_get_members_malformed_user_includes_site_group_page_row_and_value_context tests/unit/test_site_member.py::TestSiteMemberGet::test_get_members_single_page tests/unit/test_site_member.py::TestSiteMemberParse::test_parse_single_member tests/unit/test_site_member.py::TestSiteMemberParse::test_parse_ignores_nested_member_tables -q` passed 5 tests.
- `uv run --extra test pytest tests/unit/test_site_member.py -q` passed 37 tests.
- `uv run --extra test pytest tests/unit/test_site_member.py tests/unit/test_site_application.py tests/unit/test_site.py tests/unit/parsers/test_odate_parser.py tests/unit/parsers/test_user_parser.py tests/unit/test_user.py -q` passed 178 tests.
- `uv run --extra test pytest tests/unit -q` passed 847 tests.
- `uv run ruff check .`.
- `uv run ruff format --check .`.
- `uv run mypy src tests`.
- `git diff --check`.

Not run successfully: `command -v pyright` did not find a `pyright` executable.

## Acceptance Criteria

- `SiteMember.get(site, group)` raises `NoElementException` when a member-list response has a structural member row with a direct joined-at `span.odate` element whose `time_*` metadata cannot be parsed by the shared odate parser.
- The malformed joined-at error includes the site unix name, resolved member group label, page number, structural row number, `field=joined_at`, and observed direct `time_*` class value.
- `SiteMember._parse(site, html)` remains callable with its existing two-argument form.
- Valid member rows with joined-at timestamps still parse through `odate_parser(...)`.
- Rows without `span.printuser`, rows without joined-at timestamps, valid printuser values, nested member tables, row-local pager markup, response-level pagination, retry-exhausted handling, missing response-body handling, group validation, permission actions, and role-cache invalidation remain unchanged.
- No live Wikidot action, upstream Issue, upstream PR, push, raw member-list HTML, or private membership data is required for this local draft.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and the local implementation commit.
- The thread HTML report and complexity memo are refreshed after the docs commit.
- Secret and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: Wrapping shared-parser `ValueError` could hide an unexpected joined-at parsing failure. Mitigation: the wrapper preserves exception chaining with `from exc` and adds only member-list location metadata.
- Risk: Changing the shared odate parser could affect unrelated modules. Mitigation: this slice intentionally leaves `odate_parse(...)` unchanged and validates parser tests separately.
- Risk: Direct `_parse(site, html)` callers may not have group/page context. Mitigation: group and page remain optional, preserving the current direct-call contract while public `get(...)` supplies full context.

## Dependencies

- BeautifulSoup continues to expose the `class` attribute for `span.odate` elements as either a string-like value or a sequence of class values.
- The shared `odate_parse(...)` utility remains the source of truth for valid Unix timestamp extraction.
- Existing member-list markup still represents joined-at timestamps as direct second-cell `span.odate` elements when present.

## Open Questions

None for this local slice. Broader centralization of repeated `_odate_class_value(...)` helpers could be considered later only if it reduces duplication without changing parser behavior.

## Upstream-Safe Motivation

Member, moderator, and admin lists are practical browser-free site-administration inputs. If Wikidot emits a structural member row with malformed joined-at timestamp metadata, wikidot.py should return a structured parser failure naming the affected site, group, page, row, field, and observed value instead of forcing operators to infer context from a raw shared helper exception. That keeps member-list diagnostics actionable without retaining generated member-list HTML, raw response JSON, private member data, credentials, or local rollout paths.

## Local Evidence, Not For Upstream Paste

- Earlier local drafts established `SiteMember.get(site, group)` as a retry-aware and parser-scoped read path used by `Site.members`, `Site.admins`, and `Site.moderators`.
- Recent membership workflow drafts validated malformed member-list response bodies, malformed member users, permission-change action status, and role-cache invalidation after successful role changes; this slice targets only the malformed-present joined-at metadata path inside member-list parsing.
- Shared timestamp work has already covered parser-boundary diagnostics in recent changes, forum post revisions, and private-message details. Site-member lists use the same shared parser but need site/group/page/row context at their own parser boundary.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, cookies, auth JSON, raw member-list HTML, private site membership data, page names from real sites, and site contents out of upstream discussion.

## Additional Notes

This is a parser correctness and observability fix. It narrows a raw utility-parser exception into the same local exception family used by surrounding member-list response and site-administration diagnostics.
