# PR Draft: Report Malformed Site Member Response Body Types

## Summary

`SiteMember.get(site, group)`, also exposed through `site.members`, `site.admins`, and `site.moderators`, parses `membership/MembersListModule` AMC response `body` values as generated member-list HTML. Earlier local slices made site-member list reads retry-aware, scoped member rows to structural tables, ignored row-local pager markup, added retry-exhausted site/group/page context, validated missing response `body` fields, and converted malformed member user and joined-at metadata into contextual parser errors. One adjacent response-boundary gap remained: if the decoded AMC response was a dictionary with a present but non-string `body` value, the code passed that value into BeautifulSoup and leaked a low-level parser `AttributeError`.

This local slice validates present site-member list response `body` values before HTML parsing. Non-string bodies now raise site/group/page-specific `NoElementException` with `field=body`, expected type, and observed type. The diagnostic reports only compact structural context and type names; it does not include raw member-list HTML, response JSON, local rollout paths, credentials, account material, or private member data.

## Outcome

Malformed site-member list response body types now fail at the module response boundary with actionable site/group/page/type context instead of BeautifulSoup internals.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use browser-free site administration, member audits, moderator/admin checks, or membership cache refresh workflows.

## Related Issue

Builds on [031-pr-retry-member-list-fetches.md](031-pr-retry-member-list-fetches.md), [096-pr-scope-site-member-row-parsing.md](096-pr-scope-site-member-row-parsing.md), [103-pr-ignore-site-member-row-pager-markup.md](103-pr-ignore-site-member-row-pager-markup.md), [176-pr-site-member-fetch-failure-context.md](176-pr-site-member-fetch-failure-context.md), [213-pr-site-member-list-response-body-context.md](213-pr-site-member-list-response-body-context.md), [255-pr-site-member-change-group-action-status-context.md](255-pr-site-member-change-group-action-status-context.md), [270-pr-site-member-role-cache-invalidation.md](270-pr-site-member-role-cache-invalidation.md), [289-pr-site-member-user-context.md](289-pr-site-member-user-context.md), and [290-pr-site-member-joined-at-context.md](290-pr-site-member-joined-at-context.md). Those drafts established site-member acquisition as a practical retry-aware, parser-scoped, and diagnosable site-administration read path while leaving present non-string response bodies as a separate parser-entry boundary.

No upstream issue was filed from this local workspace.

## Changes

- Validate site-member list response `body` values are strings before BeautifulSoup parsing.
- Convert present non-string member-list body values into site/group/page-specific `NoElementException`.
- Preserve missing-body diagnostics, retry-exhausted behavior, group validation, pagination, structural row parsing, row-local pager filtering, malformed user diagnostics, malformed joined-at diagnostics, role mutation behavior, and site member cache behavior.

## Type Of Change

- Bug fix / diagnostics improvement
- Site member response-body type validation
- Test update

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | A site-member list response with a present non-string `body` field must fail before BeautifulSoup parsing. |
| R2 | Malformed-body-type errors must identify the affected site, resolved group label, page, `field=body`, expected type, and observed type while omitting raw generated member content. |
| R3 | Existing missing-body diagnostics, retry handling, member parsing, adjacent site/application workflows, and repository quality gates must remain compatible. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | `SiteMember.get(site, "")` raises contextual `NoElementException` when `membership/MembersListModule` returns a list-valued `body`. | `TestSiteMemberGet.test_get_members_malformed_response_body_type_includes_context` expects `Site member list response body is malformed for site: test-site, group: members, page: 1 (field=body, expected=str, actual=list)`. | Leaking BeautifulSoup `AttributeError`, silently returning an empty list, entering `user_parser`, or parsing a member row rejects this local completion claim. | Site member list reads | `tests/unit/test_site_member.py` |
| R2 | The malformed-body-type diagnostic includes only site, group, page, field name, expected type, and observed type. | The focused regression matches the full message shape and uses a synthetic list-valued body. | Including raw response JSON, generated member-list HTML, member names, credentials, local rollout paths, or account names rejects this local completion claim. | Site member diagnostics | `src/wikidot/module/site_member.py` |
| R3 | Existing site-member and adjacent site/application behavior remains green. | The site-member suite passed 38 tests, the adjacent site/member/application run passed 145 tests, and the full unit suite passed 890 tests. | Regressing missing-body diagnostics, retry exhaustion, group validation, pagination, structural row parsing, row-local pager filtering, malformed user diagnostics, malformed joined-at diagnostics, role mutations, site member lookup, or pending application workflows rejects this local completion claim. | Site administration workflows | `tests/unit/test_site_member.py`; `tests/unit/test_site.py`; `tests/unit/test_site_application.py` |

## Testing

Implemented locally in commit `7aaa390 fix(site_member): report malformed body types`.

- RED: `uv run --extra test pytest tests/unit/test_site_member.py::TestSiteMemberGet::test_get_members_malformed_response_body_type_includes_context -q` failed before the fix with BeautifulSoup `AttributeError` for the list-valued member-list body.
- GREEN: `uv run --extra test pytest tests/unit/test_site_member.py::TestSiteMemberGet::test_get_members_malformed_response_body_type_includes_context -q` passed.
- `uv run --extra test pytest tests/unit/test_site_member.py::TestSiteMemberGet::test_get_members_malformed_response_body_type_includes_context tests/unit/test_site_member.py::TestSiteMemberGet::test_get_members_missing_first_page_response_body_includes_context tests/unit/test_site_member.py::TestSiteMemberGet::test_get_members_missing_paginated_response_body_includes_context tests/unit/test_site_member.py::TestSiteMemberGet::test_get_members_single_page tests/unit/test_site_member.py::TestSiteMemberGet::test_get_members_with_pagination tests/unit/test_site_member.py::TestSiteMemberGet::test_get_members_raises_when_first_page_retry_is_exhausted tests/unit/test_site_member.py::TestSiteMemberGet::test_get_members_raises_when_paginated_retry_is_exhausted -q` passed 7 tests.
- `uv run --extra test pytest tests/unit/test_site_member.py -q` passed 38 tests.
- `uv run --extra test pytest tests/unit/test_site_member.py tests/unit/test_site.py tests/unit/test_site_application.py -q` passed 145 tests.
- `uv run --extra test pytest tests/unit -q` passed 890 tests.
- `uv run ruff check` passed.
- `uv run ruff format --check` passed with 80 files already formatted.
- `uv run mypy . --install-types --non-interactive` passed with no issues in 80 source files.
- `git diff --check` passed.

Not run successfully: `uv run pyright` failed because `pyright` was not installed in this environment.

## Acceptance Criteria

- Site-member list reads still request `membership/MembersListModule` with the existing group and page payloads.
- Missing `body` fields still raise the existing not-found diagnostic from Issue 213.
- Present non-string `body` values raise contextual `NoElementException` before BeautifulSoup parsing.
- The malformed-body-type message includes site, resolved group label, page, `field=body`, expected type, and observed type.
- The malformed-body-type message does not include raw response JSON, generated member-list HTML, member names, credentials, local rollout paths, or private account material.
- Existing retry-exhausted behavior, group validation, pagination, structural row parsing, row-local pager filtering, malformed user diagnostics, malformed joined-at diagnostics, role mutation behavior, and site member cache behavior remain unchanged.
- No live Wikidot action, upstream Issue, upstream PR, push, real member-list response body, local rollout path, account material, private member data, or generated member-list HTML is required for this local draft.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread HTML report and complexity memo are refreshed after the docs commit.
- Private-data and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: Type validation could treat a future bytes-like body as malformed. Mitigation: AMC JSON bodies are expected to decode generated HTML as strings; preserving only string input keeps the parser boundary explicit.
- Risk: Type validation could mask missing-body diagnostics. Mitigation: `None` remains on the existing missing-body path; only present non-string values use the malformed-type diagnostic.
- Risk: Diagnostics could expose generated member content. Mitigation: messages include site, group, page, field, and type names only.

## Dependencies

- The AMC connector already validates decoded response roots as dictionaries before normal module parsing; this slice targets the `body` field value within that dictionary.
- Site-member HTML parser behavior remains unchanged after a valid string body is supplied.

## Open Questions

None for this local slice. Remaining useful work should continue the broader response-body field-type audit across other modules rather than expanding this site-member change beyond its list boundary.

## Upstream-Safe Motivation

Member, moderator, and admin list discovery are practical browser-free site-administration workflows. If the generated member-list response contains a present non-string `body`, wikidot.py should report the affected site, group, page, and type mismatch before BeautifulSoup internals obscure the failure.

## Local Evidence, Not For Upstream Paste

- The RED failure showed a list-valued member-list `body` leaking BeautifulSoup `AttributeError`.
- Existing Issue 213 covered missing `body` fields but intentionally left present malformed values as a separate boundary.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, raw response JSON, generated member-list HTML, and private member data out of upstream discussion.

## Additional Notes

This is a response-body field type diagnostics fix. It preserves valid site-member behavior while making malformed present response bodies actionable without retaining generated member content.
