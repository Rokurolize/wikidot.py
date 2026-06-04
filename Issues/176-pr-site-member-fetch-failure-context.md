# PR Draft: Include Site Context In Site Member Fetch Failures

## Summary

`SiteMember.get(...)` retries the first member-list page and any paginated follow-up pages through AMC. When those retry attempts were exhausted, it raised `UnexpectedException("Cannot retrieve site members page: ...")`, which identified only the failed page number.

This follow-up preserves retry-aware member list fetching, first-page parsing, bounded pagination, admin/moderator/member group selection, row parsing, and no-partial-success behavior for failed paginated responses, but includes site unix name, resolved group label, and failed page number in exhausted member-list fetch failures.

## Related Issue

Builds on [031-pr-retry-member-list-fetches.md](031-pr-retry-member-list-fetches.md), [096-pr-scope-site-member-row-parsing.md](096-pr-scope-site-member-row-parsing.md), [103-pr-ignore-site-member-row-pager-markup.md](103-pr-ignore-site-member-row-pager-markup.md), and the recent fetch-context drafts such as [168-pr-forum-category-fetch-failure-context.md](168-pr-forum-category-fetch-failure-context.md), because those drafts established retry-aware member fetches, scoped member parsing, pager-markup rejection, and context-rich diagnostics for multi-site fetch failures.

No upstream issue was filed from this local workspace.

## Changes

- Include site unix name, group label, and page number when the first site-member page retry is exhausted.
- Include the same context when a paginated member-list retry is exhausted.
- Add a first-page exhausted retry regression and tighten the existing paginated exhausted retry regression.
- Preserve member row parsing, pager-markup rejection, retry policy, group validation, pagination, and partial-success rejection semantics.

## Type Of Change

- Bug fix / diagnostics improvement
- Site member list fetch failure context
- Test addition

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| Exhausted first-page member fetches still fail instead of falling through to parsing or direct AMC calls. | `TestSiteMemberGet.test_get_members_raises_when_first_page_retry_is_exhausted` returns `(None,)`, expects `UnexpectedException`, and asserts `site.amc_request.assert_not_called()`. | Returning an empty member list, trying direct AMC after retry exhaustion, or parsing a missing body rejects this local completion claim. |
| First-page failures identify the site, group, and page. | The focused first-page regression asserts `Cannot retrieve site members for site: test-site, group: members, page: 1`. | The RED test failed before the fix because the message only named page `1`. |
| Paginated member-list failures identify the site, group, and page. | `TestSiteMemberGet.test_get_members_raises_when_paginated_retry_is_exhausted` asserts `Cannot retrieve site members for site: test-site, group: members, page: 2`. | The RED test failed before the fix because the message only named page `2`. |
| Site member behavior remains green. | `uv run pytest tests/unit/test_site_member.py -q` passed 28 tests. | Regressions in group validation, pagination, member parsing, nested-row rejection, pager-markup rejection, or retry behavior reject this local completion claim. |
| Broad unit and static quality gates remain green. | `uv run pytest tests/unit -q`; `uv run ruff check src tests`; `uv run ruff format --check src tests`; `uv run mypy src tests`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject this local completion claim. |

## Testing

Implemented locally in commit `3089eed fix(site_member): include context in member fetch failures`.

- RED: `uv run pytest tests/unit/test_site_member.py::TestSiteMemberGet::test_get_members_raises_when_first_page_retry_is_exhausted tests/unit/test_site_member.py::TestSiteMemberGet::test_get_members_raises_when_paginated_retry_is_exhausted -q` failed before the fix because both messages only named the failed page number.
- GREEN: `uv run pytest tests/unit/test_site_member.py::TestSiteMemberGet::test_get_members_raises_when_first_page_retry_is_exhausted tests/unit/test_site_member.py::TestSiteMemberGet::test_get_members_raises_when_paginated_retry_is_exhausted -q`
- `uv run pytest tests/unit/test_site_member.py -q` passed 28 tests.
- `uv run pytest tests/unit -q` passed 724 tests.
- `uv run ruff check src tests`
- `uv run ruff format --check src tests`
- `uv run mypy src tests`
- `git diff --check`

Not run successfully: `pyright` because this environment could not find a `pyright` executable.

## Acceptance Criteria

- `SiteMember.get(...)` still validates accepted groups before issuing member-list requests.
- Retry-exhausted first-page and paginated member-list fetches still raise `UnexpectedException`.
- Those exceptions include the site unix name, resolved group label, and failed page number.
- Member row parsing, pager-markup rejection, admin/moderator/member group handling, pagination, and no-partial-success behavior remain unchanged.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Member-list collection can run across multiple Wikidot sites and groups. When a transient or persistent AMC fetch failure is exhausted, caller logs need enough context to route the failure without storing raw member-list HTML, response bodies, credentials, or private rollout details.

## Local Evidence, Not For Upstream Paste

- Earlier local drafts established retry-aware site-member list fetching, scoped member row parsing, and pager-markup rejection.
- Recent fetch-context slices showed that site/page-specific failure messages improve multi-site ledgers without changing successful behavior.
- The refreshed complexity memo continues to list collection helpers and fetch failures as follow-up leads, but this slice only claims site-member fetch diagnostics.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, raw member-list HTML, raw AMC responses, and private site/member data out of upstream discussion.

## Additional Notes

This slice intentionally does not change the member-list request payload, retry policy, group validation, pagination calculation, member row parser, pager-markup filtering, or live Wikidot behavior. It only adds site/group/page context to existing exhausted member-list fetch failures.
