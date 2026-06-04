# PR Draft: Validate Site Member List Response Bodies

## Summary

`SiteMember.get(site, group)` retrieves `membership/MembersListModule` pages for all members, admins, or moderators and parses generated member-list tables. Earlier local slices made member-list reads retry-aware, scoped member row parsing, ignored row-local pager markup, and added site/group/page context to retry-exhausted fetch failures. The remaining malformed response-body paths still read `response.json()["body"]`, so an AMC response without a `body` field leaked a raw `KeyError` before the parser could report which site, group, and page produced the malformed member-list response.

This follow-up keeps group validation, request module and payloads, retry-exhausted `None` handling, member row parsing, pagination detection, row-local pager filtering, no-partial-success behavior for failed paginated responses, and permission mutation methods unchanged. It only treats missing member-list response `body` fields as malformed list responses and raises `NoElementException` with site, group, and page context before BeautifulSoup parsing or member parsing.

## Related Issue

Builds on [031-pr-retry-member-list-fetches.md](031-pr-retry-member-list-fetches.md), [096-pr-scope-site-member-row-parsing.md](096-pr-scope-site-member-row-parsing.md), [103-pr-ignore-site-member-row-pager-markup.md](103-pr-ignore-site-member-row-pager-markup.md), and [176-pr-site-member-fetch-failure-context.md](176-pr-site-member-fetch-failure-context.md). Those drafts established member-list acquisition as a practical retry-aware site-administration workflow with parser boundaries and site/group/page diagnostics.

No upstream issue was filed from this local workspace.

## Changes

- Add a small site-member list response-body helper that reads `response.json().get("body")`.
- Convert missing first-page and paginated member-list response `body` fields into `NoElementException` with site, group, and page context.
- Preserve retry-exhausted `None` response handling as `UnexpectedException`.
- Preserve successful member parsing, valid group request payloads, response-level pagination, row-local pager filtering, partial-success rejection, and permission mutation behavior.
- Add focused regressions for missing first-page and paginated response-body handling through public `SiteMember.get(site, group)`.

## Type Of Change

- Bug fix / diagnostics improvement
- Site member list response validation
- Test coverage

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| A first-page member-list response without JSON `body` still fails before HTML parsing or member parsing. | `TestSiteMemberGet.test_get_members_missing_first_page_response_body_includes_context` returns `{}` from the first AMC response and expects `NoElementException`. | A change that raises raw `KeyError`, silently returns an empty list, or enters `user_parser` rejects this local completion claim. |
| A paginated member-list response without JSON `body` still fails with the affected page number. | `TestSiteMemberGet.test_get_members_missing_paginated_response_body_includes_context` returns a valid page 1 with pager and `{}` for page 2, then expects page-2 `NoElementException`. | A change that raises raw `KeyError`, fabricates an empty page 2, returns the page-1 member as partial success, or parses page 2 rejects this local completion claim. |
| Malformed member-list response errors identify site, group, and page. | The focused regressions assert `Site member list response body is not found for site: test-site, group: members, page: 1` and page `2`. | A generic parser exception without site/group/page context rejects this local completion claim. |
| Retry-exhausted `None` member-list responses remain distinct from malformed JSON body responses. | Existing first-page and paginated retry-exhausted tests remain green and expect `UnexpectedException`. | A change that turns skipped/exhausted `None` responses into body-validation failures rejects this local completion claim. |
| Existing site-member behavior remains green. | `uv run pytest tests/unit/test_site_member.py -q` passed 30 tests. | Regressions in group validation, pagination, member parsing, nested-row rejection, pager-markup rejection, retry behavior, or permission mutation reject this local completion claim. |
| Adjacent site/application workflows remain green. | `uv run pytest tests/unit/test_site_member.py tests/unit/test_site.py tests/unit/test_site_application.py -q` passed 119 tests. | Regressions in site accessors, recent changes, site applications, or site members reject this local completion claim. |
| Broad unit and static quality gates remain green. | `uv run pytest tests/unit -q`; `uv run ruff format src tests`; `uv run ruff check src tests`; `uv run ruff format --check src tests`; `uv run mypy src tests`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject this local completion claim. |

## Testing

Implemented locally in commit `7896469 fix(site_member): validate member list response bodies`.

- RED: `uv run pytest tests/unit/test_site_member.py::TestSiteMemberGet::test_get_members_missing_first_page_response_body_includes_context -q` failed before the fix with `KeyError: 'body'`.
- GREEN: `uv run pytest tests/unit/test_site_member.py::TestSiteMemberGet::test_get_members_missing_first_page_response_body_includes_context tests/unit/test_site_member.py::TestSiteMemberGet::test_get_members_raises_when_first_page_retry_is_exhausted tests/unit/test_site_member.py::TestSiteMemberGet::test_get_members_single_page -q` passed 3 tests.
- `uv run pytest tests/unit/test_site_member.py::TestSiteMemberGet::test_get_members_missing_first_page_response_body_includes_context tests/unit/test_site_member.py::TestSiteMemberGet::test_get_members_missing_paginated_response_body_includes_context tests/unit/test_site_member.py::TestSiteMemberGet::test_get_members_raises_when_paginated_retry_is_exhausted tests/unit/test_site_member.py::TestSiteMemberGet::test_get_members_with_pagination -q` passed 4 tests.
- `uv run pytest tests/unit/test_site_member.py -q` passed 30 tests.
- `uv run pytest tests/unit/test_site_member.py tests/unit/test_site.py tests/unit/test_site_application.py -q` passed 119 tests.
- `uv run pytest tests/unit -q` passed 749 tests.
- `uv run ruff format src tests` left 80 files unchanged.
- `uv run ruff check src tests`.
- `uv run ruff format --check src tests`.
- `uv run mypy src tests`.
- `git diff --check`.

Not run successfully: `pyright --version` because this environment could not find a `pyright` executable.

## Acceptance Criteria

- Site member list requests still use `membership/MembersListModule` with the same group and page payloads.
- Missing first-page or paginated member-list response JSON `body` raises `NoElementException` naming the site, resolved group label, and page number.
- Missing response-body handling does not convert retry-exhausted `None` responses into malformed-body failures.
- Successful member parsing, default/admin/moderator group behavior, response-level pagination, row-local pager filtering, no-partial-success retry exhaustion, and permission mutation behavior remain unchanged.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Site member, admin, and moderator inspection depends on Wikidot returning a JSON `body` field for each generated member-list module page. If that field is missing, wikidot.py should report a structured malformed-response failure with the site, group, and page, not a raw dictionary `KeyError`, so caller logs can route the failure without preserving raw response JSON, generated member-list HTML, credentials, local rollout paths, or private member data.

## Local Evidence, Not For Upstream Paste

- Earlier local drafts established site-member list acquisition as retry-aware, parser-scoped, and used through both `SiteMember.get(site, group)` and `Site.members` / `Site.admins` / `Site.moderators`.
- Recent response-body validation slices in private-message, forum-post, forum-category, and site-application modules showed the same raw `KeyError` failure mode at AMC response-body boundaries.
- The refreshed complexity memo continues to list raw response-body boundaries in `forum_thread`, `site_member`, `page_file`, `page_revision`, `forum_post_revision`, `page`, and `site` as follow-up leads, but this slice only claims site-member list response-body validation.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, raw response JSON, generated member-list HTML, and private site/member data out of upstream discussion.

## Additional Notes

This slice intentionally does not change request module names, request payloads, retry policy, retry-exhausted `None` handling, group validation, pagination calculation, member row parser, pager-markup filtering, `Site.members`, `Site.admins`, `Site.moderators`, permission mutation methods, or live Wikidot behavior. It only converts missing site-member list response `body` fields into site/group/page-context `NoElementException` failures before parser work.
