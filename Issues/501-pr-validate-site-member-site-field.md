# PR Draft: Validate SiteMember Site Field

## Summary

`SiteMember` records carry the parent `Site` used by browser-free member-list reads, role-change actions, returned-status diagnostics, role-cache invalidation, generated membership ledgers, and local fixtures. Earlier local slices validated member-list fetch retries, row scoping, response-body diagnostics, parser-side member user and joined-at handling, role-change action status, role-cache invalidation, member lookup inputs, role-change action users, direct `SiteMember.user`, direct `SiteMember.joined_at`, and the adjacent `SiteApplication.site` parent field. One direct record-state gap remained: `SiteMember(..., site=...)` still accepted arbitrary non-`Site` values such as `None`, booleans, strings, dictionaries, and arbitrary objects.

This change validates `SiteMember.site` at initialization and immediately before role-change action work. Malformed parent-site values now raise `ValueError("site must be a Site")` before invalid member state can be stored or a mutated public field can reach login checks, AMC request construction, returned-status diagnostics, or role-cache mutation. Valid `Site` parents, member-list parsing, user validation, joined-at validation, role-change behavior, role-cache invalidation, site application behavior, site workflows, and user workflows remain unchanged.

## Outcome

Callers cannot silently construct site-member records with malformed parent-site state, and a later `member.site` mutation is rejected before login or AMC work. Parser-created members and valid direct `SiteMember(...)` construction keep the existing member inventory and role-change behavior.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use browser-free member inventories, `site.members`, `site.moderators`, `site.admins`, direct `SiteMember.get(site, group)` calls, generated membership ledgers, role-change automation, site-access audits, local fixtures, or serialized and rehydrated member rows.

## Current Evidence

Site-member drafts [031-pr-retry-member-list-fetches.md](031-pr-retry-member-list-fetches.md), [096-pr-scope-site-member-row-parsing.md](096-pr-scope-site-member-row-parsing.md), [103-pr-ignore-site-member-row-pager-markup.md](103-pr-ignore-site-member-row-pager-markup.md), [176-pr-site-member-fetch-failure-context.md](176-pr-site-member-fetch-failure-context.md), [213-pr-site-member-list-response-body-context.md](213-pr-site-member-list-response-body-context.md), [255-pr-site-member-change-group-action-status-context.md](255-pr-site-member-change-group-action-status-context.md), [270-pr-site-member-role-cache-invalidation.md](270-pr-site-member-role-cache-invalidation.md), [289-pr-site-member-user-context.md](289-pr-site-member-user-context.md), [290-pr-site-member-joined-at-context.md](290-pr-site-member-joined-at-context.md), [323-pr-site-member-response-body-type-context.md](323-pr-site-member-response-body-type-context.md), [357-pr-validate-site-member-lookup-username.md](357-pr-validate-site-member-lookup-username.md), [372-pr-validate-site-member-lookup-user-id.md](372-pr-validate-site-member-lookup-user-id.md), [410-pr-validate-site-member-action-users.md](410-pr-validate-site-member-action-users.md), [448-pr-validate-site-member-user-field.md](448-pr-validate-site-member-user-field.md), and [499-pr-validate-site-member-joined-at-field.md](499-pr-validate-site-member-joined-at-field.md) establish member acquisition, parser diagnostics, response diagnostics, role-change response validation, role-cache synchronization, lookup validation, action-user preflight, and direct member-row state as practical operational boundaries.

Adjacent constructor-hardening drafts [439-pr-validate-site-change-site-field.md](439-pr-validate-site-change-site-field.md), [475-pr-validate-forum-thread-collection-site-field.md](475-pr-validate-forum-thread-collection-site-field.md), [476-pr-validate-forum-category-collection-site-field.md](476-pr-validate-forum-category-collection-site-field.md), [477-pr-validate-page-collection-site-field.md](477-pr-validate-page-collection-site-field.md), [478-pr-validate-site-accessor-parent-sites.md](478-pr-validate-site-accessor-parent-sites.md), [486-pr-validate-page-constructor-site.md](486-pr-validate-page-constructor-site.md), and [500-pr-validate-site-application-site-field.md](500-pr-validate-site-application-site-field.md) establish the local pattern for validating direct parent-site fields instead of relying only on parser boundaries or mocks.

## Related Issue / Non-Duplicate Analysis

This is not a duplicate of Issue 448. Issue 448 validates only `SiteMember.user` at construction and preserves action-specific ID/name validation before role-change requests. This slice validates the separate parent `Site` object that supplies the client, AMC action surface, site name diagnostics, and role-cache mutation target.

This is not a duplicate of Issue 499. Issue 499 validates only the optional `SiteMember.joined_at` timestamp field. This slice validates the parent-site field and preserves the optional timestamp semantics.

This is not a duplicate of Issue 500. Issue 500 validates `SiteApplication.site` for pending-application records and explicitly left the analogous `SiteMember.site` boundary for a separate duplicate analysis and fixture-tightening slice. This change applies the same parent-state pattern to member rows and role-change actions.

No upstream issue was filed from this local workspace.

## Changes

- Add `_validate_site_member_site(...)` with a circular-import-safe local `Site` import.
- Update `SiteMember.__post_init__` to reject non-`Site` parent objects.
- Revalidate `self.site` inside `_change_group(...)` after invalid-event validation and before user validation, login checks, AMC requests, returned-status handling, or cache mutation.
- Use the validated `site` local for login, AMC request dispatch, and moderator/admin cache invalidation.
- Tighten site-member unit fixtures so valid member tests use real `Site` instances with request methods stubbed.
- Add focused regressions for malformed constructor sites and mutated action-time sites.

## Type Of Change

- Input validation
- Public dataclass constructor behavior hardening
- Site member mutation preflight hardening
- Test fixture tightening

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `SiteMember(site=None)`, `True`, `"test-site"`, `{"unix_name": "test-site"}`, and `object()` must raise `ValueError("site must be a Site")` when every other constructor field is valid. |
| R2 | Valid `Site` parents must remain valid constructor inputs, and parser-created `SiteMember` rows must retain the original parent site. |
| R3 | `SiteMember.to_moderator()` and the shared role-change path must reject a mutated non-`Site` `member.site` with `ValueError("site must be a Site")` before login checks, AMC requests, returned-status handling, or role-cache changes. |
| R4 | Existing member-list parsing, pagination, retry behavior, response diagnostics, malformed member-user diagnostics, malformed joined-at diagnostics, user validation, joined-at validation, role-change behavior, role-cache invalidation, site application behavior, site workflows, and user workflows must remain unchanged. |
| R5 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private membership data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R6 | Focused RED/GREEN, site-member tests, adjacent site/member/application/user tests, full unit tests, lint, format, mypy, pyright, and whitespace gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Malformed constructor site values fail at the public dataclass boundary. | `TestSiteMemberDataclass.test_init_rejects_malformed_sites` failed RED for 5 malformed values because the constructor did not raise, then passed GREEN after validation was added. | Accepting missing values, booleans, site names, dictionaries, arbitrary objects, or emitting member rows with non-`Site` parent state rejects this local completion claim. | SiteMember constructor | `src/wikidot/module/site_member.py`, `tests/unit/test_site_member.py` |
| R2 | Valid parent-site semantics stay green. | Existing constructor, parser, and member-list tests passed after valid fixtures used real `Site` objects with stubbed request methods. | Rejecting valid `Site` objects, losing the parent site during `SiteMember.get(...)`, or changing stored user/joined-at fields rejects this local completion claim. | Parser-created and manually created members | `tests/unit/test_site_member.py` |
| R3 | Mutated non-site parent state fails before side-effect surfaces. | `TestSiteMemberChangeGroup.test_change_group_rejects_malformed_site_before_login` failed RED by reaching mocked AMC response handling through a mutated mock site, then passed GREEN and asserts no login check, no AMC request, and no role-cache mutation on the malformed site. | Calling `client.login_check()`, calling `amc_request(...)`, mutating `_moderators` or `_admins`, or leaking mock-derived status diagnostics rejects this local completion claim. | Site member role-change methods | `src/wikidot/module/site_member.py`, `tests/unit/test_site_member.py` |
| R4 | Existing adjacent workflows remain green. | `tests/unit/test_site_member.py` passed 57 tests, adjacent site/site-member/site-application/user tests passed 398 tests, and the full unit suite passed 2219 tests. | Regressing member-list acquisition, pagination, retry behavior, response-body diagnostics, malformed member-user parser diagnostics, malformed joined-at parser diagnostics, member lookup, role-cache invalidation, site application processing, site read/write helpers, or user profile workflows rejects this local completion claim. | Site member and adjacent workflows | `tests/unit` |
| R5 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level tests only. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, raw member-list HTML, private member names, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R6 | Repository quality gates pass in the local dependency environment. | Full ruff, format, mypy, pyright, unit, and whitespace checks passed. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `53da37d fix(site_member): validate member site`.

- RED: `uv run pytest tests/unit/test_site_member.py::TestSiteMemberDataclass::test_init_rejects_malformed_sites -q` failed 5 tests before the fix; every malformed `site` value reported `DID NOT RAISE`.
- GREEN constructor: `uv run pytest tests/unit/test_site_member.py::TestSiteMemberDataclass::test_init_rejects_malformed_sites -q` passed 5 tests.
- RED action-time mutation: `uv run pytest tests/unit/test_site_member.py::TestSiteMemberChangeGroup::test_change_group_rejects_malformed_site_before_login -q` failed before `_change_group(...)` revalidation because the mutated mock site reached mocked AMC response handling and raised `WikidotStatusCodeException` instead of the expected `ValueError`.
- GREEN focused: `uv run pytest tests/unit/test_site_member.py::TestSiteMemberDataclass::test_init_rejects_malformed_sites tests/unit/test_site_member.py::TestSiteMemberChangeGroup::test_change_group_rejects_malformed_site_before_login -q` passed 6 tests.
- `uv run pytest tests/unit/test_site_member.py -q` passed 57 tests.
- `uv run pytest tests/unit/test_site.py tests/unit/test_site_member.py tests/unit/test_site_application.py tests/unit/test_user.py -q` passed 398 tests.
- `uv run ruff check src/wikidot/module/site_member.py tests/unit/test_site_member.py` passed.
- `uv run ruff format --check src/wikidot/module/site_member.py tests/unit/test_site_member.py` passed with 2 files already formatted.
- `uv run mypy src/wikidot/module/site_member.py tests/unit/test_site_member.py` passed with no issues in 2 source files.
- `uv run pyright src/wikidot/module/site_member.py tests/unit/test_site_member.py` passed with 0 errors, 0 warnings, and 0 informations.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 86 files already formatted.
- `uv run mypy src tests` passed with no issues in 86 source files.
- `uv run pyright src tests` passed with 0 errors, 0 warnings, and 0 informations.
- `uv run pytest tests/unit -q` passed 2219 tests.
- `git diff --check` passed.

## Acceptance Criteria

- `SiteMember(site=None)`, `True`, `"test-site"`, `{"unix_name": "test-site"}`, and `object()` raise `ValueError("site must be a Site")`.
- Valid `Site` instances remain valid as `SiteMember.site`.
- Parser-created rows from `SiteMember.get(site, group)` retain the original valid `Site` parent.
- Role-change actions reject a mutated non-`Site` parent before login checks, AMC requests, returned-status handling, or role-cache invalidation.
- Existing member-list parsing, response-body diagnostics, malformed member-user diagnostics, malformed joined-at diagnostics, user/joined-at validation, role-change behavior, role-cache invalidation, site application behavior, site workflows, and user workflows remain green.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private membership data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Risks And Mitigations

- Risk: Tests could keep using permissive mocks that no longer reflect the public contract. Mitigation: valid site-member fixtures now construct real `Site` objects and only stub network-facing request methods.
- Risk: Constructor validation could be confused with live-site validation. Mitigation: this change only checks the local parent object type and does not contact Wikidot, validate permissions, or change authentication behavior.
- Risk: Action-time validation could accidentally change invalid-event ordering. Mitigation: `_change_group(...)` still rejects invalid event strings before checking the parent site, preserving the existing invalid-event behavior.

## Dependencies

- Valid member-list parser output continues to be created from a real `Site` object supplied to `SiteMember.get(site, group)`.
- Existing `Site` constructor validation remains responsible for site scalar fields such as `id`, `title`, `unix_name`, `domain`, and `ssl_supported`.
- Existing action-user preflight remains responsible for member `id` and `name` validation before mutation requests.

## Open Questions

None for this local slice.

## Upstream-Safe Motivation

`SiteMember.site` is the parent object behind browser-free member inventories, role-change actions, action diagnostics, and role-cache invalidation. Parser paths already pass a real `Site` object into created member rows. Constructor and action-time validation keep malformed local parent state out of manually constructed or mutated records without changing member-list acquisition, parser selectors, role-change payloads, returned-status handling, cache behavior, or live Wikidot interactions.

## Local Evidence, Not For Upstream Paste

- Local rollout-backed work repeatedly used browser-free member-list acquisition, generated membership state, role-change actions, role-cache invalidation, direct member lookup, site application processing, and tests that construct `SiteMember` records directly.
- Existing local drafts covered site member fetch retry behavior, parser row scoping, response-body diagnostics, malformed parsed member users, malformed parsed joined-at timestamps, action-status validation, role-cache invalidation, member lookup inputs, action-user preflight, direct user validation, direct joined-at validation, and adjacent site-application parent validation, but did not cover direct `SiteMember(site=...)` construction or action-time parent-site mutation.
- The focused RED failures showed invalid constructor site values were accepted as dataclass state. The action-time RED showed a mutated mock parent reached role-change response handling before validation. The GREEN regressions cover missing, boolean, string, dictionary, and arbitrary object values plus a mutated action-time mock site.
- This slice only validates stored site-member parent type at construction and before mutation actions. It does not change member-list acquisition, parser selectors, response-body diagnostics, member-user parsing, joined-at parsing, role-change payload construction, returned-status handling, role-cache invalidation semantics for valid sites, live site behavior, or client authentication.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw member-list HTML, private member names, page source text, forum source text, private messages, and private site data out of upstream discussion.

## Additional Notes

The change intentionally rejects malformed parent objects instead of accepting site-like mocks or dictionaries. Tests and downstream callers should construct a real `Site` object and stub network-facing request methods when unit-level isolation is needed.
