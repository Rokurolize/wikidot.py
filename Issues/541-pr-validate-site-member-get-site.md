# PR Draft: Validate SiteMember Get Site Argument

## Summary

`SiteMember.get(site, group)`, also exposed through `site.members`, `site.admins`, and `site.moderators`, is the static member-list read boundary for browser-free site membership inspection. Earlier local slices validated member-list retries, parser scoping, response-body diagnostics, parsed member user and joined-at diagnostics, role-change action status, role-cache invalidation, member lookup inputs, action-user preflight, direct `SiteMember` field state, and malformed `SiteMember.site` before mutation actions. One adjacent public read-input gap remained: direct calls such as `SiteMember.get(None, "")`, `"test-site"`, dictionaries, booleans, or arbitrary objects reached `site.amc_request_with_retry(...)` and leaked raw `AttributeError`.

This change reuses the existing `_validate_site_member_site(...)` helper at the `SiteMember.get(...)` entry point after group validation and before any member-list request work. Malformed `site` arguments now raise `ValueError("site must be a Site")` deterministically, while valid member-list acquisition, group validation, request payloads, pagination, response diagnostics, parser diagnostics, role-change behavior, site accessors, and adjacent site/member/application/user workflows remain unchanged.

## Outcome

Direct member-list callers now get the same deterministic parent-site preflight used by stored `SiteMember` records, instead of incidental attribute errors from malformed call inputs.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who call `SiteMember.get(site, group)` directly or use generated site/member automation where a malformed deserialized or fixture-provided site object should fail before AMC request construction.

## Current Evidence

Local rollout-backed drafts repeatedly identify site membership reads and administration as practical workflow surfaces. Existing drafts [031-pr-retry-member-list-fetches.md](031-pr-retry-member-list-fetches.md), [096-pr-scope-site-member-row-parsing.md](096-pr-scope-site-member-row-parsing.md), [103-pr-ignore-site-member-row-pager-markup.md](103-pr-ignore-site-member-row-pager-markup.md), [176-pr-site-member-fetch-failure-context.md](176-pr-site-member-fetch-failure-context.md), [213-pr-site-member-list-response-body-context.md](213-pr-site-member-list-response-body-context.md), [289-pr-site-member-user-context.md](289-pr-site-member-user-context.md), [290-pr-site-member-joined-at-context.md](290-pr-site-member-joined-at-context.md), [323-pr-site-member-response-body-type-context.md](323-pr-site-member-response-body-type-context.md), [448-pr-validate-site-member-user-field.md](448-pr-validate-site-member-user-field.md), [499-pr-validate-site-member-joined-at-field.md](499-pr-validate-site-member-joined-at-field.md), and [501-pr-validate-site-member-site-field.md](501-pr-validate-site-member-site-field.md) establish this path as active and already hardened around response, parser, stored-state, and mutation surfaces.

This is not a duplicate of Issue 501. Issue 501 validates direct `SiteMember(site=...)` construction and revalidates mutated stored `member.site` before role-change actions. It does not validate the caller-provided `site` argument to the static `SiteMember.get(site, group)` read helper before request work.

No upstream issue was filed from this local workspace.

## Changes

- Add a focused regression for malformed `SiteMember.get(site=...)` inputs.
- Validate the `site` argument with `_validate_site_member_site(...)` after existing group validation and before `amc_request_with_retry(...)`.
- Preserve invalid-group precedence, valid member-list request payloads, pagination, response-body diagnostics, parser diagnostics, role-change behavior, and site accessors.

## Type Of Change

- Input validation
- Public read-boundary hardening
- Site member list preflight
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `SiteMember.get(None, "")`, `True`, `"test-site"`, `{"unix_name": "test-site"}`, and `object()` must raise `ValueError("site must be a Site")` before member-list request work. |
| R2 | Invalid `group` values must still raise `ValueError("Invalid group")` before validating or using the site argument. |
| R3 | Valid `SiteMember.get(site, group)` acquisition, pagination, request payloads, response-body diagnostics, parser diagnostics, and returned `SiteMember.site` parent state must remain unchanged. |
| R4 | Site member, adjacent site/application/user workflows, full unit tests, lint, format, mypy, pyright, and whitespace gates must pass before claiming this local implementation complete. |
| R5 | The draft and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private membership data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Malformed direct member-list `site` inputs fail at the public read boundary. | `TestSiteMemberGet.test_get_rejects_malformed_site_before_request` failed RED for all 5 malformed values with raw `AttributeError`, then passed GREEN after validation was added. | Reaching `site.amc_request_with_retry`, accepting site-like dictionaries, returning an empty list, or leaking raw attribute errors rejects this local completion claim. | `SiteMember.get(...)` | `src/wikidot/module/site_member.py`, `tests/unit/test_site_member.py` |
| R2 | Existing invalid-group ordering is preserved. | Focused GREEN included `TestSiteMemberGet.test_get_invalid_group_raises`. | Requiring a valid site before rejecting an invalid group or changing the error message rejects this local completion claim. | Group validation | `src/wikidot/module/site_member.py`, `tests/unit/test_site_member.py` |
| R3 | Valid member-list behavior remains stable. | Focused GREEN included `test_get_members_single_page`; full `tests/unit/test_site_member.py` passed 62 tests. | Changing request payloads, retry handling, pagination, parser output, response diagnostics, or returned parent-site state rejects this local completion claim. | Site member list reads | `tests/unit/test_site_member.py` |
| R4 | Existing adjacent workflows remain green. | Adjacent site/member/application/user tests passed 434 tests, full unit tests passed 2563 tests, and repository lint, format, mypy, pyright, and whitespace gates passed. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |
| R5 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level synthetic state; this draft contains no credentials, cookies, auth JSON, raw response bodies, private member names, or live site data. | Using real account names, credentials, cookies, auth JSON, sandbox details, raw rollout paths, pushes, upstream Issues, upstream PRs, live Wikidot actions, raw member-list HTML, private member names, or private site data rejects this local completion claim. | Test and draft privacy | this draft |

## Testing

Implemented locally in commit `c1085a4 fix(site_member): validate member list site`.

- RED: `uv run pytest tests/unit/test_site_member.py::TestSiteMemberGet::test_get_rejects_malformed_site_before_request -q` failed 5 tests before the fix because malformed sites reached `site.amc_request_with_retry(...)` and leaked raw `AttributeError`.
- GREEN focused: `uv run pytest tests/unit/test_site_member.py::TestSiteMemberGet::test_get_rejects_malformed_site_before_request tests/unit/test_site_member.py::TestSiteMemberGet::test_get_invalid_group_raises tests/unit/test_site_member.py::TestSiteMemberGet::test_get_members_single_page -q` passed 7 tests.
- `uv run pytest tests/unit/test_site_member.py -q` passed 62 tests.
- `uv run pytest tests/unit/test_site.py tests/unit/test_site_member.py tests/unit/test_site_application.py tests/unit/test_user.py -q` passed 434 tests.
- `uv run pytest tests/unit -q` passed 2563 tests.
- `uv run ruff check src/wikidot/module/site_member.py tests/unit/test_site_member.py` passed.
- `uv run ruff format --check src/wikidot/module/site_member.py tests/unit/test_site_member.py` passed with 2 files already formatted.
- `uv run mypy src/wikidot/module/site_member.py tests/unit/test_site_member.py` passed with no issues in 2 source files.
- `uv run pyright src/wikidot/module/site_member.py tests/unit/test_site_member.py` passed with 0 errors, 0 warnings, and 0 informations.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run pyright src/wikidot/module/site_member.py tests/unit/test_site_member.py` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- Malformed direct `SiteMember.get(site=...)` inputs raise `ValueError("site must be a Site")`.
- Invalid groups still raise `ValueError("Invalid group")`.
- Valid member-list reads, pagination, response diagnostics, parser diagnostics, and returned member parent state stay unchanged.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private membership data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Risks And Mitigations

- Risk: The new validation could change invalid-group precedence. Mitigation: validation remains after the existing group check, and the focused GREEN command includes the invalid-group test.
- Risk: Tests could accept site-like mocks or dictionaries as a valid public contract. Mitigation: the regression uses malformed values that previously leaked raw attribute errors, while existing valid fixtures keep real `Site` instances with request methods stubbed.

## Dependencies

- Existing `_validate_site_member_site(...)` remains the canonical local parent-site validator.
- Existing `Site` constructor validation remains responsible for site scalar fields such as `id`, `title`, `unix_name`, `domain`, and `ssl_supported`.

## Open Questions

None for this local slice.

## Upstream-Safe Motivation

`SiteMember.get(...)` is the direct read entry point behind member, moderator, and admin list discovery. Validating the supplied parent `Site` before request work gives generated callers and fixtures deterministic errors for malformed inputs without changing live Wikidot behavior, request shape, group semantics, parsing, retries, or mutation paths.

## Local Evidence, Not For Upstream Paste

- The focused RED failures showed malformed direct `site` arguments crossing the public static read boundary and leaking `AttributeError` from `site.amc_request_with_retry`.
- This slice only validates the `SiteMember.get(...)` caller-provided parent type. It does not change member-list acquisition, parser selectors, response-body diagnostics, member-user parsing, joined-at parsing, role-change payload construction, returned-status handling, role-cache invalidation semantics, live site behavior, or client authentication.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw member-list HTML, private member names, page source text, forum source text, private messages, and private site data out of upstream discussion.
