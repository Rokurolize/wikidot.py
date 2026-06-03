# PR Draft: Scope Site Member Row Parsing

## Summary

`SiteMember._parse(...)` parses `membership/MembersListModule` output into `SiteMember` records used by `SiteMember.get(...)`, `Site.members`, `Site.moderators`, and `Site.admins`.

Before this fix, the parser used response-wide descendant selectors: `html.select("table tr")`, `row.select("td")`, `tds[0].select_one(".printuser")`, and `tds[1].select_one(".odate")`. If a structural member row contained nested member-like table markup before the real member, the nested row could be parsed as a separate site member and the outer row could read the nested `printuser` instead of the structural user. The focused regression produced two members, both for `Fake User`, even though the response had one structural member row whose real user was `Real User`.

This fix keeps request construction, group selection, retry behavior, pagination, permission mutation methods, and site cache properties unchanged, but treats only top-level member tables, direct rows, direct row cells, and direct structural user/date spans as member-list structure.

## Related Issue

Builds on [031-pr-retry-member-list-fetches.md](031-pr-retry-member-list-fetches.md), because that draft established member-list acquisition as a practical read-heavy workflow rather than speculative code. It also follows the membership-management line in [032-pr-retry-application-list-fetches.md](032-pr-retry-application-list-fetches.md), [053-pr-decline-application-status-text.md](053-pr-decline-application-status-text.md), [079-pr-reuse-application-response-body.md](079-pr-reuse-application-response-body.md), and [090-pr-ignore-nested-application-body-markup.md](090-pr-ignore-nested-application-body-markup.md). The parser-boundary motivation matches [081-pr-ignore-forum-content-pseudo-posts.md](081-pr-ignore-forum-content-pseudo-posts.md), [086-pr-ignore-nested-category-tables.md](086-pr-ignore-nested-category-tables.md), [087-pr-ignore-nested-thread-tables.md](087-pr-ignore-nested-thread-tables.md), [091-pr-scope-recent-changes-comment-markup.md](091-pr-scope-recent-changes-comment-markup.md), [092-pr-scope-listpages-field-markup.md](092-pr-scope-listpages-field-markup.md), [093-pr-scope-who-rated-vote-parsing.md](093-pr-scope-who-rated-vote-parsing.md), [094-pr-scope-page-revision-row-cells.md](094-pr-scope-page-revision-row-cells.md), and [095-pr-scope-page-file-row-parsing.md](095-pr-scope-page-file-row-parsing.md).

No upstream issue was filed from this local workspace.

## Changes

- Ignore member-list tables nested inside another table.
- Parse direct structural `tr` rows from a top-level member table or its direct `tbody`.
- Parse only direct `td` cells from each structural row.
- Parse the member user from a direct `span.printuser` in the first structural cell.
- Parse the joined-at timestamp from a direct `span.odate` in the second structural cell when exactly two structural cells are present.
- Add a regression where nested member-like table markup inside a structural member cell does not create extra `SiteMember` records or override the real member.
- Preserve rows without users, header rows, missing joined-at timestamps, grouped member requests, paginated member requests, retry exhaustion behavior, and permission-change actions.

## Type Of Change

- Bug fix
- Parser robustness improvement
- Test addition/modification

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| Member rows should come from top-level member-list tables, not nested tables. | `TestSiteMemberParse.test_parse_ignores_nested_member_tables` inserts a nested member-like table inside the structural first cell and asserts only one member is returned. | The RED test failed before the fix because two members were returned. |
| User and joined-at metadata should come from direct structural cells. | The same focused test asserts the parsed user is `Real User` and the joined-at value comes from the structural second cell despite nested `Fake User` and fake date markup. | The RED test failed before the fix because descendant parsing returned `Fake User`. |
| Existing site-member behavior should remain green. | `uv run pytest tests/unit/test_site_member.py -q` passed 26 tests, and `uv run pytest tests/unit/test_site_application.py tests/unit/test_site.py tests/unit/test_site_member.py -q` passed 100 tests. | Regressions in no-date parsing, header skipping, groups, pagination, retry exhaustion, site properties, application handling, or permission changes reject the local completion claim. |
| Broad unit and static quality gates remain green. | `uv run pytest tests/unit -q`; `uv run ruff check .`; `uv run ruff format --check .`; `uv run mypy .`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject the local completion claim. |

## Testing

Implemented locally in commit `aa983a2 fix(site_member): scope member row parsing`.

- RED: `uv run pytest tests/unit/test_site_member.py::TestSiteMemberParse::test_parse_ignores_nested_member_tables -q` failed before the fix because `len(members)` was `2` and both parsed users came from nested `Fake User` markup.
- GREEN: `uv run pytest tests/unit/test_site_member.py::TestSiteMemberParse::test_parse_ignores_nested_member_tables -q`
- `uv run pytest tests/unit/test_site_member.py::TestSiteMemberParse::test_parse_single_member tests/unit/test_site_member.py::TestSiteMemberParse::test_parse_member_without_joined_at tests/unit/test_site_member.py::TestSiteMemberParse::test_parse_ignores_nested_member_tables -q` passed 3 tests.
- `uv run pytest tests/unit/test_site_member.py -q` passed 26 tests.
- `uv run pytest tests/unit/test_site_application.py tests/unit/test_site.py tests/unit/test_site_member.py -q` passed 100 tests.
- `uv run pytest tests/unit -q` passed 648 tests.
- `uv run ruff check .`
- `uv run ruff format --check .`
- `uv run mypy .`
- `git diff --check`

Not run: `uv run pyright src tests` because this environment could not find a `pyright` executable on PATH in earlier checks.

## Acceptance Criteria

- Site-member parsing ignores tables nested inside another table.
- Nested member-like rows inside a structural member row cannot create extra `SiteMember` records.
- Nested `span.printuser` or `span.odate` markup inside a structural member cell cannot override the structural member user or joined-at timestamp.
- Existing valid member rows with and without joined-at timestamps still parse into the same public `SiteMember` objects.
- Existing all-member, admin, moderator, pagination, retry exhaustion, cached `Site` property, and permission-change behavior remains unchanged.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Member, moderator, and admin list inspection is a practical site administration workflow. The `membership/MembersListModule` response has a fixed table shape, so the parser should use top-level generated table rows and direct cells as the structural boundary. That avoids confusing nested table markup with actual site-member rows while preserving the public `SiteMember` behavior.

## Local Evidence, Not For Upstream Paste

- Earlier local draft [031-pr-retry-member-list-fetches.md](031-pr-retry-member-list-fetches.md) established member-list acquisition as a repeatedly hardened site inspection path.
- Site membership and application drafts [032-pr-retry-application-list-fetches.md](032-pr-retry-application-list-fetches.md), [053-pr-decline-application-status-text.md](053-pr-decline-application-status-text.md), [079-pr-reuse-application-response-body.md](079-pr-reuse-application-response-body.md), and [090-pr-ignore-nested-application-body-markup.md](090-pr-ignore-nested-application-body-markup.md) show the same operational area has been used and improved in local rollout-backed work.
- Parser-boundary drafts [081-pr-ignore-forum-content-pseudo-posts.md](081-pr-ignore-forum-content-pseudo-posts.md) through [095-pr-scope-page-file-row-parsing.md](095-pr-scope-page-file-row-parsing.md) established the concrete failure class: broad descendant selectors can confuse generated module structure with nested markup.
- The refreshed complexity scan continues to flag `src/wikidot/module/site_member.py` row parsing as an audit-worthy read-heavy parser surface.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, site membership details, and page content out of upstream discussion.

## Additional Notes

This slice does not change `membership/MembersListModule` request payloads, retry policy, pagination detection, member groups, permission mutation requests, `Site.members`, `Site.admins`, or `Site.moderators`. It only narrows member row and cell discovery to structural elements.
