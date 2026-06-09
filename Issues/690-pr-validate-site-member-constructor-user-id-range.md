# PR Draft: Validate SiteMember Constructor User ID Range

## Summary

`SiteMember(...)` records already validate the parent site, member user object type, member/site client coherence, joined-at type, role-change action-user ID type, role-change action-user name type, role-change action-user ID range, returned action status, mapped target errors, and role-cache behavior. One constructor gap remained: a valid member `User` could be mutated, fixture-loaded, or rehydrated with a negative retained `user.id` and then stored in a new `SiteMember` row. That corrupted row would not fail until a later role-change action, despite parser-created member rows and direct `User` construction already enforcing non-negative user IDs.

This change validates negative retained member user IDs at the `SiteMember(...)` constructor boundary. Negative retained member IDs now raise `ValueError("member.user.id must be non-negative")`, valid zero member IDs remain accepted in direct rows, and action-time validation still owns the stricter member ID type/name checks before membership mutation payloads are built.

## Outcome

Direct `SiteMember(...)` rows cannot store impossible negative member user IDs. Valid parser-created rows, same-client direct rows, zero-ID compatibility, malformed site/user/joined-at diagnostics, member/site client coherence, role-change action preflights, action-status diagnostics, mapped target errors, role-cache behavior, and adjacent site/application/user/private-message workflows remain unchanged.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use browser-free member inventories, generated membership ledgers, local fixtures, serialized member rows, migration checks, moderation workflows, site-access audits, or rehydrated `SiteMember` objects before role administration.

## Current Evidence

Site-member drafts [031-pr-retry-member-list-fetches.md](031-pr-retry-member-list-fetches.md), [096-pr-scope-site-member-row-parsing.md](096-pr-scope-site-member-row-parsing.md), [103-pr-ignore-site-member-row-pager-markup.md](103-pr-ignore-site-member-row-pager-markup.md), [176-pr-site-member-fetch-failure-context.md](176-pr-site-member-fetch-failure-context.md), [213-pr-site-member-list-response-body-context.md](213-pr-site-member-list-response-body-context.md), [255-pr-site-member-change-group-action-status-context.md](255-pr-site-member-change-group-action-status-context.md), [270-pr-site-member-role-cache-invalidation.md](270-pr-site-member-role-cache-invalidation.md), [289-pr-site-member-user-context.md](289-pr-site-member-user-context.md), [290-pr-site-member-joined-at-context.md](290-pr-site-member-joined-at-context.md), [323-pr-site-member-response-body-type-context.md](323-pr-site-member-response-body-type-context.md), [357-pr-validate-site-member-lookup-username.md](357-pr-validate-site-member-lookup-username.md), [372-pr-validate-site-member-lookup-user-id.md](372-pr-validate-site-member-lookup-user-id.md), [410-pr-validate-site-member-action-users.md](410-pr-validate-site-member-action-users.md), [448-pr-validate-site-member-user-field.md](448-pr-validate-site-member-user-field.md), [499-pr-validate-site-member-joined-at-field.md](499-pr-validate-site-member-joined-at-field.md), [501-pr-validate-site-member-site-field.md](501-pr-validate-site-member-site-field.md), [541-pr-validate-site-member-get-site.md](541-pr-validate-site-member-get-site.md), [605-pr-validate-site-member-user-client.md](605-pr-validate-site-member-user-client.md), and [688-pr-validate-site-member-action-user-id-range.md](688-pr-validate-site-member-action-user-id-range.md) establish member acquisition, parser diagnostics, constructor field validation, member/site coherence, role-change behavior, action-user preflight, and role-cache synchronization as practical workflow surfaces.

Related user-ID drafts [647-pr-validate-non-negative-user-ids.md](647-pr-validate-non-negative-user-ids.md), [646-pr-validate-non-negative-quickmodule-user-ids.md](646-pr-validate-non-negative-quickmodule-user-ids.md), [648-pr-validate-non-negative-site-member-lookup-user-ids.md](648-pr-validate-non-negative-site-member-lookup-user-ids.md), [685-pr-validate-private-message-send-recipient-id-range.md](685-pr-validate-private-message-send-recipient-id-range.md), [686-pr-validate-site-invite-user-id-range.md](686-pr-validate-site-invite-user-id-range.md), [687-pr-validate-site-application-user-id-range.md](687-pr-validate-site-application-user-id-range.md), [688-pr-validate-site-member-action-user-id-range.md](688-pr-validate-site-member-action-user-id-range.md), and [689-pr-validate-site-application-constructor-user-id-range.md](689-pr-validate-site-application-constructor-user-id-range.md) establish direct user-ID range validation, QuickModule user-ID range validation, member lookup user-ID filter validation, private-message recipient ID range validation, site invitation target ID range validation, site application action-time applicant ID range validation, site member role-change user ID range validation, and site application constructor user ID range validation as active operational boundaries.

This slice is not a duplicate of those drafts. Issue 448 validates that `SiteMember.user` is an `AbstractUser`, but it does not validate retained member user ID range. Issue 605 validates that the member user belongs to the parent site client, not the retained ID range. Issue 688 validates negative retained `member.user.id` at the role-change action boundary, but a direct `SiteMember(...)` row could still store the corrupted user until action time. Issue 647 validates direct `User` and `DeletedUser` construction, but it cannot cover a valid user object whose public `id` is corrupted after construction and then stored in a member row. Issue 689 validates the adjacent `SiteApplication` constructor boundary, not site members.

## Related Issue / Non-Duplicate Analysis

Builds directly on [410-pr-validate-site-member-action-users.md](410-pr-validate-site-member-action-users.md), [448-pr-validate-site-member-user-field.md](448-pr-validate-site-member-user-field.md), [501-pr-validate-site-member-site-field.md](501-pr-validate-site-member-site-field.md), [605-pr-validate-site-member-user-client.md](605-pr-validate-site-member-user-client.md), [647-pr-validate-non-negative-user-ids.md](647-pr-validate-non-negative-user-ids.md), and [688-pr-validate-site-member-action-user-id-range.md](688-pr-validate-site-member-action-user-id-range.md).

No upstream issue was filed from this local workspace.

## Changes

- Validate negative retained member IDs inside the existing `SiteMember` user object validator used by `__post_init__`.
- Reject retained constructor member IDs `-1` and `-100` with `ValueError("member.user.id must be non-negative")`.
- Preserve valid retained member ID `0` for direct `SiteMember(...)` construction.
- Keep action-time malformed ID type and malformed name validation in the existing role-change helper.
- Preserve existing site validation, member object validation, member/site client validation, joined-at validation, action-status diagnostics, mapped target errors, role-cache behavior, and successful role-change behavior.

## Type Of Change

- State validation
- Site member constructor hardening
- Retained user identity integrity
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `SiteMember(site=site, user=user, joined_at=...)` must reject retained `user.id=-1` and `user.id=-100` with `ValueError("member.user.id must be non-negative")` before storing the member row. |
| R2 | Valid retained member ID `0` must remain accepted in direct `SiteMember(...)` construction. |
| R3 | Existing action-time negative-ID regressions must continue to prove post-construction mutation is rejected before login or AMC request work. |
| R4 | Existing malformed site validation, non-`AbstractUser` member validation, member/site client validation, joined-at validation, malformed action-user ID/name validation, action-status diagnostics, mapped target errors, role-cache behavior, and adjacent site/member/application/user/private-message workflows must remain unchanged. |
| R5 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private member data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R6 | Focused RED/GREEN, site-member tests, adjacent site/member/application/user/private-message tests, full unit tests, lint, format, type, pyright, and whitespace gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Negative retained member IDs fail at the direct constructor boundary. | `test_init_rejects_negative_user_id` failed RED for `-1` and `-100` with `DID NOT RAISE`, then passed GREEN after constructor user-ID range validation was added. | Accepting a negative retained member ID, storing the row, or deferring the failure only to role-change helpers rejects this local completion claim. | `SiteMember` constructor | `src/wikidot/module/site_member.py`, `tests/unit/test_site_member.py` |
| R2 | Valid zero member IDs remain valid direct constructor state. | `test_init_accepts_zero_user_id` passed RED and GREEN, asserting the stored member ID remains `0`. | Rejecting zero, converting it to `None`, or changing valid row construction rejects this local completion claim. | `SiteMember` constructor | `tests/unit/test_site_member.py` |
| R3 | Post-construction mutation remains covered at action time. | Existing role-change negative-ID tests now construct a valid row, mutate `member.user.id`, and pass by rejecting before login and AMC request work across all four role-change helpers. | Losing action-time mutation coverage, calling `login_check()`, sending `ManageSiteMembershipAction`, mutating role caches, or raising returned-status diagnostics rejects this local completion claim. | `SiteMember` role-change helpers | `tests/unit/test_site_member.py` |
| R4 | Existing site-member behavior and adjacent workflows remain green. | `tests/unit/test_site_member.py` passed 79 tests, adjacent site/member/application/user/private-message coverage passed 736 tests, and full unit coverage passed 3405 tests. | Regressing parser-created members, constructor site/user/joined-at diagnostics, client coherence, action preflights, action-status handling, mapped target errors, role-cache behavior, site/application/user/private-message workflows, or any unit test rejects this local completion claim. | Site member and adjacent workflows | `tests/unit` |
| R5 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level tests only with synthetic sites and members. | Using credentials, cookies, auth JSON, private member names, raw rollout paths, live Wikidot actions, pushes, upstream Issues, or upstream PRs rejects this local completion claim. | Test and draft privacy | this draft |
| R6 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN, site-member/adjacent/full-unit tests, ruff, format check, mypy, temporary pyright, and `git diff --check` passed. | Test, lint, format, type, pyright, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `265813d fix(site_member): validate constructor user id range`.

- RED: `uv run pytest tests/unit/test_site_member.py::TestSiteMemberDataclass -k user_id -q` selected 3 constructor user-ID tests; 2 negative retained-member-ID cases failed before the fix with `DID NOT RAISE`, while 1 zero-ID compatibility guard passed.
- GREEN: the same focused command passed 3 tests after constructor user-ID range validation was added.
- `uv run ruff format src/wikidot/module/site_member.py tests/unit/test_site_member.py` left both files unchanged.
- `uv run pytest tests/unit/test_site_member.py -q` passed 79 tests.
- `uv run pytest tests/unit/test_site.py tests/unit/test_site_member.py tests/unit/test_site_application.py tests/unit/test_user.py tests/unit/test_private_message.py -q` passed 736 tests.
- `uv run pytest tests/unit -q` passed 3405 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `git diff --check` passed.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run --with pyright pyright` passed with 0 errors, 0 warnings, and 0 informations.

## Acceptance Criteria

- `SiteMember(...)` raises `ValueError("member.user.id must be non-negative")` when the member user's retained `id` is `-1` or `-100`.
- Negative retained member IDs fail before the member row is stored by direct construction.
- Valid retained member ID `0` remains accepted by direct construction.
- Existing action-time role-change negative-ID tests still prove post-construction mutation fails before `site.client.login_check()`, `site.amc_request(...)`, returned action-status parsing, mapped target errors, or role-cache mutation.
- Existing malformed site validation, non-`AbstractUser` member validation, member/site client ownership validation, joined-at validation, action-user ID type validation, action-user name validation, valid moderator/admin role changes, returned action-status validation, mapped target errors, role-cache invalidation, site application workflows, user behavior, and private-message send behavior remain green.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private member data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.
- Private-data and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: Rehydrated member rows with negative retained member IDs now fail during construction instead of later role-change work. Mitigation: negative user IDs are impossible identity state; failing before storing corrupted member rows is more deterministic.
- Risk: Valid zero IDs could be accidentally rejected if validation were changed to positive-only. Mitigation: the focused zero-ID constructor guard asserts `member.user.id == 0`.
- Risk: Action-time mutation coverage could be lost after constructor hardening. Mitigation: the role-change negative-ID test now constructs a valid row first and mutates `member.user.id` afterward across all four public helpers.
- Risk: Validation precedence could regress earlier member diagnostics. Mitigation: the constructor range check still runs after the existing `AbstractUser` check, while stricter ID type/name checks remain in the existing action helper; the site-member, adjacent, and full tests remain green.

## Dependencies

- Existing `User` constructor validation remains unchanged.
- Existing site-member site validation, member object validation, member/site client validation, joined-at validation, action-user ID type validation, action-user name validation, action-status validation, mapped target errors, and role-cache behavior remain unchanged.

## Open Questions

None for this local slice. Remaining useful work should continue with fresh duplicate-checked public input boundaries, parser diagnostics, result ergonomics, action/read boundaries, retained cache/collection state, downstream mutable user-state preflights, or complexity candidates outside this now-covered `SiteMember` constructor user-ID range boundary.

## Upstream-Safe Motivation

`SiteMember` is the durable row shape behind member inventories, membership ledgers, site-access audits, moderation workflows, and role-change automation. Parser-created member users come from structured printuser parsing and direct `User` construction already rejects negative IDs. Constructor-side range validation keeps corrupted fixture-loaded or rehydrated member identity out of stored member rows while preserving zero-ID compatibility, valid parser-created rows, client coherence, joined-at validation, and action-time mutation preflights.

## Local Evidence, Not For Upstream Paste

- Local rollout-backed work established site members as a practical workflow through member-list retry, parser diagnostics, response-body diagnostics, member field validation, member/site client validation, role-change action-status validation, member action-time ID range validation, and role-cache invalidation.
- Existing local drafts covered non-`AbstractUser` members, malformed action-time member ID types, malformed action-time member names, member client mismatch, direct user constructor ID ranges, QuickModule user IDs, member lookup user-ID filters, private-message send recipient ID ranges, site invitation target ID ranges, site-application action-time applicant ID ranges, and site-member role-change user ID ranges; they did not validate negative retained `User.id` values at the direct `SiteMember(...)` constructor boundary.
- The focused RED failure showed negative retained member IDs could be stored in direct member rows. The GREEN regressions cover constructor negative rejection, zero-ID constructor compatibility, action-time post-construction mutation coverage, site-member behavior, adjacent site/member/application/user/private-message workflows, and full unit compatibility.
- This slice only validates negative retained member IDs at the `SiteMember` constructor boundary. It does not change member-list parsing, site invitation actions, site application actions, member lookup filters, user construction, profile lookup, live site behavior, pushes, upstream Issues, or upstream PRs.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, private member data, raw action responses, source text from real sites, and private site data out of upstream discussion.

## Additional Notes

The implementation intentionally extends `_validate_site_member_user(...)` instead of calling the full action helper from `__post_init__`. The constructor now rejects impossible negative IDs while the role-change path continues to own stricter payload-specific ID type and member-name requirements.
