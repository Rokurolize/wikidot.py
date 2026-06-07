# PR Draft: Validate Site Member User Client

## Summary

`SiteMember` records carry both the parent `Site` and the member `user`. Existing site-member slices validate parser-side user extraction, direct `user` type, direct `site` type, direct `joined_at` type, and role-change action-user ID/name requirements. One constructor and mutation coherence gap remained: direct `SiteMember(...)` construction could combine `site=site_a` with `user=User(client=site_b.client, ...)`, and a later `member.user` mutation to another client context could reach role-change login and AMC response handling.

This change validates `SiteMember.user.client` against `SiteMember.site.client` during `SiteMember.__post_init__` and again in the shared role-change path after existing site/user shape checks but before login, AMC requests, action-status handling, or role-cache mutation. Mismatches raise `ValueError("member.user must belong to the site")`. Valid parser-created member rows, same-client direct rows, existing malformed field diagnostics, member-list pagination, role-change behavior, and adjacent site/member/application/user workflows remain unchanged.

## Outcome

Site-member rows cannot store or act on a member user from a different client context than the parent site.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use browser-free member inventories, `site.members`, `site.moderators`, `site.admins`, direct `SiteMember.get(site, group)` calls, generated membership ledgers, role-change automation, site-access audits, migration checks, local fixtures, or serialized and rehydrated member rows.

## Current Evidence

Local rollout-backed drafts repeatedly identify site membership and role administration as practical workflow surfaces. Existing drafts [031-pr-retry-member-list-fetches.md](031-pr-retry-member-list-fetches.md), [096-pr-scope-site-member-row-parsing.md](096-pr-scope-site-member-row-parsing.md), [103-pr-ignore-site-member-row-pager-markup.md](103-pr-ignore-site-member-row-pager-markup.md), [176-pr-site-member-fetch-failure-context.md](176-pr-site-member-fetch-failure-context.md), [213-pr-site-member-list-response-body-context.md](213-pr-site-member-list-response-body-context.md), [255-pr-site-member-change-group-action-status-context.md](255-pr-site-member-change-group-action-status-context.md), [270-pr-site-member-role-cache-invalidation.md](270-pr-site-member-role-cache-invalidation.md), [289-pr-site-member-user-context.md](289-pr-site-member-user-context.md), [290-pr-site-member-joined-at-context.md](290-pr-site-member-joined-at-context.md), [323-pr-site-member-response-body-type-context.md](323-pr-site-member-response-body-type-context.md), [357-pr-validate-site-member-lookup-username.md](357-pr-validate-site-member-lookup-username.md), [372-pr-validate-site-member-lookup-user-id.md](372-pr-validate-site-member-lookup-user-id.md), [410-pr-validate-site-member-action-users.md](410-pr-validate-site-member-action-users.md), [448-pr-validate-site-member-user-field.md](448-pr-validate-site-member-user-field.md), [499-pr-validate-site-member-joined-at-field.md](499-pr-validate-site-member-joined-at-field.md), [501-pr-validate-site-member-site-field.md](501-pr-validate-site-member-site-field.md), and [541-pr-validate-site-member-get-site.md](541-pr-validate-site-member-get-site.md) establish member acquisition, parser diagnostics, response diagnostics, role-change response validation, role-cache synchronization, lookup validation, direct record-state validation, and action-time preflights as active boundaries.

The parser path already constructs member users with the parent site's client by calling the shared user parser as `user_parser(site.client, user_elem)`. The new rule brings direct constructor and action-time mutation behavior in line with that parser invariant.

## Related Issue / Non-Duplicate Analysis

This is not a duplicate of Issue 448. Issue 448 validates that `SiteMember.user` is an `AbstractUser`; it explicitly does not validate site, joined-at, user ID/name, role membership, lookup behavior, or client authentication at construction time. This slice validates the relationship between a valid `Site` and a valid `AbstractUser`.

This is not a duplicate of Issue 501. Issue 501 validates that `SiteMember.site` is a `Site` and revalidates mutated site state before role-change actions; it does not compare the valid site object with the valid user object.

This is not a duplicate of Issue 410. Issue 410 validates action-specific user type, ID, and name before role-change side effects; it does not prevent a valid action user from belonging to another client context.

No upstream issue was filed from this local workspace.

## Changes

- Add `SiteMember` user-client coherence validation.
- Reject direct rows where `user.client is not site.client` with `ValueError("member.user must belong to the site")`.
- Revalidate the same coherence in `_change_group(...)` before login checks, AMC requests, action-status handling, or role-cache mutation.
- Preserve existing validation order for malformed site, malformed user type, malformed joined-at, invalid event, and action-specific user ID/name diagnostics.
- Tighten unit fixtures so valid synthetic members and parser mocks use the same client as their synthetic site.
- Preserve side-effect-free construction and preflight-only action validation: the new check compares object identity only and does not perform login checks, HTTP requests, user lookups, coercion, or site mutation.

## Type Of Change

- Input validation
- Public dataclass constructor behavior hardening
- Site-member role-change preflight hardening
- Membership ledger identity integrity
- Test fixture tightening

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `SiteMember(site=site_a, user=User(client=site_b.client, ...), ...)` must reject the mismatched member client with `ValueError("member.user must belong to the site")` before storing record state. |
| R2 | Role-change methods must reject a later `member.user` mutation to another client context with the same `ValueError` before login checks, AMC requests, action-status handling, or role-cache mutation. |
| R3 | Valid direct `SiteMember(...)` rows where `user.client is site.client` and parser-created member rows must remain valid. |
| R4 | Existing malformed `site`, malformed `user`, malformed `joined_at`, invalid event, and malformed action-user ID/name diagnostics must remain unchanged. |
| R5 | Existing member-list parsing, pagination, retry behavior, response diagnostics, malformed member-user diagnostics, malformed joined-at diagnostics, role-cache invalidation, site application behavior, site workflows, and user workflows must remain unchanged. |
| R6 | The draft and tests must not require live Wikidot actions, credentials, cookies, auth JSON, raw rollout paths, pushes, upstream Issues, or upstream PRs. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Constructor member/client mismatches fail at the public dataclass boundary. | `TestSiteMemberDataclass.test_init_rejects_user_from_different_client` failed RED with `DID NOT RAISE`, then passed GREEN after `SiteMember.__post_init__` called the coherence preflight. | Accepting a valid `User` object from another client context, emitting a member row whose site and user client disagree, or deferring the mismatch to later use rejects this local completion claim. | `SiteMember` constructor | `src/wikidot/module/site_member.py`, `tests/unit/test_site_member.py` |
| R2 | Mutated member/client mismatches fail before role-change side effects. | `TestSiteMemberChangeGroup.test_change_group_rejects_user_from_different_client_before_login` failed RED by reaching mocked role-change status handling with `WikidotStatusCodeException`, then passed GREEN and asserts no login check and no AMC request. | Calling `site.client.login_check()`, calling `site.amc_request(...)`, mutating role caches, or leaking returned-status diagnostics rejects this local completion claim. | Site member role-change methods | `src/wikidot/module/site_member.py`, `tests/unit/test_site_member.py` |
| R3 | Existing valid constructor, parser, and role-change rows stay green. | `tests/unit/test_site_member.py` passed 64 tests after valid fixtures and parser mocks used `site.client`. | Rejecting same-client direct users, replacing user objects, coercing users, breaking parser-created rows, or requiring live authentication rejects this local completion claim. | `SiteMember` constructor, parser, and role changes | `tests/unit/test_site_member.py` |
| R4 | Existing diagnostics stay stable. | Focused site-member coverage passed existing malformed site, malformed user, malformed joined-at, invalid event, malformed action-user, and malformed action-site tests. | Changing existing `ValueError` diagnostics, validating coherence before malformed field checks, or accepting previously rejected malformed values rejects this local completion claim. | SiteMember validation order | `tests/unit/test_site_member.py` |
| R5 | Existing adjacent workflows remain green. | Adjacent site/site-member/site-application/user coverage passed 461 tests, and full unit coverage passed 2731 tests. | Regressing member-list acquisition, pagination, retry behavior, response-body diagnostics, parser diagnostics, member lookup, role-cache invalidation, site application processing, site read/write helpers, or user profile workflows rejects this local completion claim. | Site member and adjacent workflows | `tests/unit` |
| R6 | No live auth material or private site state is needed to prove the behavior. | The regressions use synthetic `Site` and `User` objects only, and this draft contains no credentials, cookies, auth JSON, raw response bodies, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. | Using real account names, credentials, cookies, auth JSON, sandbox details, raw rollout paths, pushes, upstream Issues, upstream PRs, live Wikidot actions, raw member-list HTML, private member names, or private site data rejects this local completion claim. | Test and draft privacy | this draft |

## Testing

Implemented locally in commit `a295756 fix(site_member): validate member user client`.

- RED: `uv run pytest tests/unit/test_site_member.py::TestSiteMemberDataclass::test_init_rejects_user_from_different_client tests/unit/test_site_member.py::TestSiteMemberChangeGroup::test_change_group_rejects_user_from_different_client_before_login -q` failed before the fix. The constructor case reported `DID NOT RAISE`; the action-time case reached mocked role-change status handling and raised `WikidotStatusCodeException` instead of the expected preflight `ValueError`.
- GREEN regression: the same focused command passed 2 tests.
- Site-member coverage: `uv run pytest tests/unit/test_site_member.py -q` passed 64 tests.
- Adjacent site/member/application/user coverage: `uv run pytest tests/unit/test_site.py tests/unit/test_site_member.py tests/unit/test_site_application.py tests/unit/test_user.py -q` passed 461 tests.
- `uv run pytest tests/unit -q` passed 2731 tests.
- `uv run ruff format src/wikidot/module/site_member.py tests/unit/test_site_member.py` left 2 files unchanged.
- `uv run ruff check src/wikidot/module/site_member.py tests/unit/test_site_member.py` passed.
- `uv run ruff check` passed.
- `uv run ruff format --check` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run pyright src tests` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `SiteMember(site=site_a, user=User(client=site_b.client, ...), ...)` raises `ValueError("member.user must belong to the site")`.
- Role-change methods reject a mutated `member.user` from another client context before login checks, AMC requests, action-status handling, or role-cache mutation.
- Valid direct rows where `user.client is site.client` remain valid.
- Existing malformed `user` values still raise `ValueError("member.user must be an AbstractUser")`.
- Existing malformed `site`, malformed `joined_at`, invalid event, and malformed action-user ID/name diagnostics remain unchanged.
- Existing parser-created member rows still produce valid `SiteMember` records.
- Existing member-list parsing, retry/pagination behavior, response-body diagnostics, role-change behavior, role-cache invalidation, site application behavior, site workflows, and user workflows remain green.
- The new tests use unit-level synthetic values only and do not require live Wikidot, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

`SiteMember` is the durable row shape behind browser-free member inventories, role-change actions, role-cache invalidation, membership ledgers, site-access audits, and migration checks. A member row is site-scoped, and parser-created users already come from the parent site's client. Constructor and action-time coherence validation keep direct fixtures, rehydrated rows, and mutated public fields from mixing site and member client contexts while preserving the normal parser and role-change paths.

## Local Evidence, Not For Upstream Paste

- The focused RED failures showed direct `SiteMember(site=site_a, user=User(client=site_b.client, ...), ...)` construction silently accepted a contradictory row, and action-time mutation to another-client user reached role-change response handling before validation.
- Existing local drafts covered member-list fetch retry, parser row scoping, response-body diagnostics, parser-side user extraction, direct user type validation, direct site type validation, joined-at validation, action-user ID/name validation, role-change action-status diagnostics, and role-cache invalidation, but did not validate coherence between a valid member user object and a valid parent site.
- This slice only validates constructor-time and action-time member user/client coherence. It does not change member-list request construction, parser selectors, group handling, response-body validation, user parser semantics, joined-at parsing, role-change payload fields, returned-status handling for valid rows, role-cache invalidation semantics, live site behavior, authentication semantics, or request helper behavior.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw login response bodies, raw member-list HTML, private member names, page source text from real sites, and private site data out of upstream discussion.

## Additional Notes

The check intentionally compares client object identity rather than user IDs, usernames, site IDs, UNIX names, or authentication state. The parser path and the rest of the object graph preserve client identity, and identity comparison avoids network lookups, login checks, and ambiguous cross-client equivalence rules.
