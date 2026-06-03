# PR Draft: Ignore Site Member Row Pager Markup

## Summary

`SiteMember.get(...)` reads the first `membership/MembersListModule` response, parses member rows, then discovers a `div.pager` to decide whether additional member-list pages should be requested.

Before this fix, pager discovery used the first response-wide `div.pager`. If rendered member-row content contained pager-like markup, acquisition treated that content markup as structural member-list pagination and requested phantom pages. The focused regression inserted a row-local `div.pager` containing links `1` and `2`; before the fix, `SiteMember.get(...)` fetched page 2 and returned the same member twice.

This fix preserves real member-list pagination while ignoring pager-like markup rendered inside structural member rows.

## Related Issue

Builds on [031-pr-retry-member-list-fetches.md](031-pr-retry-member-list-fetches.md) and [096-pr-scope-site-member-row-parsing.md](096-pr-scope-site-member-row-parsing.md), because those drafts established member-list acquisition as a practical local workflow and direct member rows as the parsing boundary.

The pager-boundary failure class is adjacent to [097-pr-ignore-forum-content-pager-markup.md](097-pr-ignore-forum-content-pager-markup.md), [098-pr-ignore-thread-description-pager-markup.md](098-pr-ignore-thread-description-pager-markup.md), [099-pr-ignore-recent-change-comment-pager-markup.md](099-pr-ignore-recent-change-comment-pager-markup.md), [100-pr-ignore-listpages-field-pager-markup.md](100-pr-ignore-listpages-field-pager-markup.md), and [101-pr-ignore-private-message-row-pager-markup.md](101-pr-ignore-private-message-row-pager-markup.md): all of these fixes prevent content-local `div.pager` markup from becoming a structural pagination control.

No upstream issue was filed from this local workspace.

## Changes

- Add member-list pager discovery that skips `div.pager` elements located inside a structural member row.
- Detect structural member-row ancestry using the same direct-row/direct-first-cell/direct-`span.printuser` shape already used by `SiteMember._parse(...)`.
- Add a regression where member-row pager-like markup does not request page 2 or duplicate the member.
- Preserve real structural member-list pagination, non-numeric pager handling, retry behavior, group selection, member parsing, site member lookup helpers, and permission mutation methods.

## Type Of Change

- Bug fix
- Parser robustness improvement
- Test addition/modification

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| Pager-like markup inside a structural member row should not be treated as member-list pagination. | `TestSiteMemberGet.test_get_members_ignores_member_row_pager_markup` inserts row-local links `1` and `2` and asserts one member plus one AMC request. | The RED test failed before the fix because `SiteMember.get(...)` returned two members after a phantom page-2 request. |
| Real structural member-list pagination should continue to work. | The neighboring pagination tests still cover page-2 acquisition, exhausted paginated retry errors, and non-numeric pager links. | If a real response-level pager stops queuing page 2 or exhausted page 2 no longer raises, the focused pager cluster rejects the local completion claim. |
| Existing member, site lookup, and permission workflows should remain green. | `uv run pytest tests/unit/test_site_member.py -q` passed 27 tests, and `uv run pytest tests/unit/test_site_member.py tests/unit/test_site.py -q` passed 84 tests. | Regressions in member parsing, group selection, site member lookup, recent changes, page helpers, or permission mutation tests reject the local completion claim. |
| Broad unit and static quality gates remain green. | `uv run pytest tests/unit -q`; `uv run ruff check .`; `uv run ruff format --check .`; `uv run mypy .`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject the local completion claim. |

## Testing

Implemented locally in commit `c1285ad fix(site_member): ignore row pager markup`.

- RED: `uv run pytest tests/unit/test_site_member.py::TestSiteMemberGet::test_get_members_ignores_member_row_pager_markup -q` failed before the fix because `len(members)` was `2` after a phantom page-2 request.
- GREEN: `uv run pytest tests/unit/test_site_member.py::TestSiteMemberGet::test_get_members_ignores_member_row_pager_markup -q`
- `uv run pytest tests/unit/test_site_member.py::TestSiteMemberGet::test_get_members_with_pagination tests/unit/test_site_member.py::TestSiteMemberGet::test_get_members_raises_when_paginated_retry_is_exhausted tests/unit/test_site_member.py::TestSiteMemberGet::test_get_members_ignores_non_numeric_pager_links tests/unit/test_site_member.py::TestSiteMemberGet::test_get_members_ignores_member_row_pager_markup -q` passed 4 tests.
- `uv run pytest tests/unit/test_site_member.py -q` passed 27 tests.
- `uv run pytest tests/unit/test_site_member.py tests/unit/test_site.py -q` passed 84 tests.
- `uv run pytest tests/unit -q` passed 655 tests.
- `uv run ruff check src/wikidot/module/site_member.py tests/unit/test_site_member.py`
- `uv run ruff format --check src/wikidot/module/site_member.py tests/unit/test_site_member.py`
- `uv run mypy src/wikidot/module/site_member.py tests/unit/test_site_member.py`
- `uv run ruff check .`
- `uv run ruff format --check .`
- `uv run mypy .`
- `git diff --check`

Not run: `uv run pyright src tests` because this environment could not find a `pyright` executable on PATH in earlier checks.

## Acceptance Criteria

- `div.pager` markup inside a structural member row is treated as row content only.
- Row-local pager-like links cannot queue additional `membership/MembersListModule` pages.
- Real response-level member-list pagination still queues additional pages.
- Non-numeric pager links still leave acquisition on the first page only.
- Exhausted retry for a real additional member-list page still raises the existing page-numbered `UnexpectedException`.
- Existing member parsing, group selection, member-list retry behavior, site member lookup helpers, and permission mutation behavior remain unchanged.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Member-list rows are structural records, but user-rendered or content-adjacent HTML inside those rows may contain pager-like markup. `SiteMember.get(...)` should use only structural member-list pagination controls to decide whether more member pages exist, and it should ignore pager-like row content.

## Local Evidence, Not For Upstream Paste

- Earlier local drafts [031-pr-retry-member-list-fetches.md](031-pr-retry-member-list-fetches.md) and [096-pr-scope-site-member-row-parsing.md](096-pr-scope-site-member-row-parsing.md) established member-list acquisition and direct member rows as practical local targets.
- Pager-boundary drafts [097-pr-ignore-forum-content-pager-markup.md](097-pr-ignore-forum-content-pager-markup.md), [098-pr-ignore-thread-description-pager-markup.md](098-pr-ignore-thread-description-pager-markup.md), [099-pr-ignore-recent-change-comment-pager-markup.md](099-pr-ignore-recent-change-comment-pager-markup.md), [100-pr-ignore-listpages-field-pager-markup.md](100-pr-ignore-listpages-field-pager-markup.md), and [101-pr-ignore-private-message-row-pager-markup.md](101-pr-ignore-private-message-row-pager-markup.md) established response-wide pager discovery as a repeated parser-boundary risk.
- The refreshed complexity scan continues to flag parser/request loops as audit-worthy paths, and member-list acquisition still had response-wide pager discovery before this fix.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, and member identities out of upstream discussion.

## Additional Notes

This slice does not change request payloads, retry policy, page-number parsing, group selection, `SiteMember._parse(...)`, `SiteMember` fields, site cache properties, or permission mutation methods. It only narrows which `div.pager` can control additional member-list page requests.
